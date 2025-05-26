from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import app as chatbot_graph
from app.utils import get_latest_messages, save_message
import asyncio
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
security = HTTPBearer()
app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    reset: bool = False

class ChatResponse(BaseModel):
    response: str

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme.")
    return credentials.credentials

from httpx import HTTPStatusError

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    token: str = Depends(get_token)
):
    session_id = request.session_id
    message = request.message
    reset = request.reset

    try:
        history = await get_latest_messages(session_id, token)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: invalid token for get_latest_messages"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while fetching message history: {str(e)}"
        )

    if reset or not history:
        session = {
            "thread_id": session_id,
            "history": []
        }
    else:
        session = {
            "thread_id": session_id,
            "history": history
        }

    config = {"configurable": {"thread_id": session["thread_id"]}}
    state = {
        "question": message,
        "history": session["history"]
    }

    if asyncio.iscoroutinefunction(chatbot_graph.invoke):
        result = await chatbot_graph.invoke(state, config=config)
    else:
        result = chatbot_graph.invoke(state, config=config)

    # Tangani error 401 juga saat menyimpan pesan
    try:
        await save_message(session_id, message, "human", token)
        await save_message(session_id, result["answer"], "ai", token)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: invalid token for save_message"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while saving messages: {str(e)}"
        )

    return ChatResponse(response=result["answer"])

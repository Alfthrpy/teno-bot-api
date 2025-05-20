from fastapi import FastAPI
from pydantic import BaseModel
from agent import app as chatbot_graph
from utils import get_latest_messages, save_message
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


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    token: str = Depends(get_token)
):
    session_id = request.session_id
    message = request.message
    reset = request.reset

    # Masukkan token ke get_latest_messages
    history = await get_latest_messages(session_id, token)

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

    # Masukkan token ke save_message
    await save_message(session_id, message, "human", token)
    await save_message(session_id, result["answer"], "ai", token)

    return ChatResponse(response=result["answer"])

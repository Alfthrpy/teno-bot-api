from fastapi import FastAPI
from pydantic import BaseModel
from agent import app as chatbot_graph
from utils import get_latest_messages, save_message
import asyncio

app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    reset: bool = False

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    message = request.message
    reset = request.reset

    history = await get_latest_messages(session_id)

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

    # Jika agent.invoke() support async, pakai await
    if asyncio.iscoroutinefunction(chatbot_graph.invoke):
        result = await chatbot_graph.invoke(state, config=config)
    else:
        # fallback ke sync
        result = chatbot_graph.invoke(state, config=config)

    # Simpan pesan ke database
    await save_message(session_id, message, "user")
    await save_message(session_id, result["answer"], "bot")

    return ChatResponse(response=result["answer"])

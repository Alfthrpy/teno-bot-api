import httpx  # ganti dari requests ke httpx (karena httpx support async)
from dotenv import load_dotenv
import os
load_dotenv()

TOKEN_ACCOUNT = os.getenv("LANGSMITH_API_KEY")
async def get_latest_messages(session_id: str, limit: int = 6):
    url = f'https://tenangin-backend.vercel.app/api/chatbot/sessions/{session_id}/messages'
    headers = {
    f"Authorization": "Bearer {TOKEN_ACCOUNT}"
    }   
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data[-limit:]
    

async def save_message(session_id: str, message: str, sender: str):
    url = f'https://tenangin-backend.vercel.app/api/chatbot/sessions/{session_id}/messages'
    headers = {
    f"Authorization": "Bearer {TOKEN_ACCOUNT}",
    }
    data = {
        "sender": sender,
        "message": message,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
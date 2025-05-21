import httpx  # ganti dari requests ke httpx (karena httpx support async)
from dotenv import load_dotenv
import os
load_dotenv()

async def get_latest_messages(session_id: str,token:str, limit: int = 6):
    url = f'https://tenangin-backend.vercel.app/api/chatbot/sessions/{session_id}/messages'
    headers = {
        "Authorization": f"Bearer {token}"
    }   
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Ambil data terakhir dan ubah format ke role-content
        formatted = [
            {
                "role": msg.get("sender"), 
                "content": msg.get("message")
            }
            for msg in data[-limit:]
        ]

        return formatted

    

async def save_message(session_id: str, message: str, sender: str, token:str):
    url = f'https://tenangin-backend.vercel.app/api/chatbot/sessions/{session_id}/messages'
    headers = {
    "Authorization": f"Bearer {token}",
    }
    data = {
        "sender": sender,
        "message": message,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
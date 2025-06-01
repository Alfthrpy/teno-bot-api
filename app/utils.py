import httpx  # ganti dari requests ke httpx (karena httpx support async)
from dotenv import load_dotenv
import os
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_KEY")

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
    
async def get_profile(session_id: str):
    url = f'{SUPABASE_URL}/rest/v1/rpc/get_profile_by_session'
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_API_KEY}" 
    }
    payload = {
        "session_id": session_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return format_profiles(response.json())
    

def format_profiles(profiles):
    result = []
    for item in profiles:
        formatted = (
            f"- Nama Lengkap: {item.get('full_name', '')}\n"
            f"- Umur: {item.get('age', '')}\n"
            f"- Jenis Kelamin: {item.get('gender', '')}\n"
            f"- Alamat: {item.get('address', '')}\n"
            f"- Tempat Lahir: {item.get('place_of_birth', '')}\n"
            f"- Tanggal Lahir: {item.get('date_of_birth', '')}\n"
            f"- Tentang Saya: {item.get('about_me', '')}"
        )
        result.append(formatted)
    return "\n\n".join(result)
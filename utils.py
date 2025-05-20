import httpx  # ganti dari requests ke httpx (karena httpx support async)

async def get_latest_messages(session_id: str, limit: int = 6):
    # url = f'https://tenangin-backend.vercel.app/api/chatbot/sessions/{session_id}/messages'
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(url)
    #     response.raise_for_status()
    #     data = response.json()
        # return data[-limit:]
        return []
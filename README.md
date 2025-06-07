# TenoBot API

This repository contains the source code for the TenoBot API, the backend service powering "Teno," an empathetic AI counselor for the **Tenangin** application.

The API is built using **FastAPI** to handle high-performance, asynchronous requests. It implements a **Retrieval-Augmented Generation (RAG)** pipeline using **LangChain** and **LangGraph** to provide context-aware, stateful conversations. For its RAG capabilities, the service utilizes a **FAISS** vector store with Indonesian **SBERT** embeddings to retrieve relevant documents, enhancing the context for Google's **Gemini** language model. To deliver a personalized experience, the API securely fetches user profiles from a Supabase backend and maintains conversation history through a dedicated external service, enabling natural and flowing dialogue. The main endpoint is secured and requires a Bearer Token for authentication.

## Architecture Overview

The API operates in the following sequence:
1.  A `POST` request is sent to the `/chat` endpoint with a `session_id`, `message`, and an auth token.
2.  The API fetches the user's profile from Supabase and the recent message history from the Tenangin backend service using the `session_id`.
3.  The user's message and history are passed to a LangGraph agent.
4.  **Retrieve Node**: The agent first uses the FAISS vector store to find documents relevant to the user's query and recent conversation history.
5.  **Generate Node**: The retrieved context, user profile, and conversation history are compiled into a detailed prompt for the Gemini LLM. The model generates an empathetic, human-like response.
6.  The new user message and the AI's response are saved back to the Tenangin backend to maintain conversation state.
7.  The final AI-generated response is returned to the client.

## Tech Stack & Key Libraries

* **Backend**: FastAPI
* **AI Framework**: LangChain, LangGraph
* **Language Model**: Google Gemini (`gemini-2.0-flash`)
* **Embeddings**: Sentence-Transformers (Indonesian SBERT)
* **Vector Store**: FAISS (Facebook AI Similarity Search)
* **External Services**:
    * Supabase (for user profiles)
    * Tenangin Backend (for message history)
* **Async HTTP**: httpx
* **Deployment**: Vercel

## Local Setup and Installation

### Prerequisites

* Python 3.9+
* A local copy of the FAISS vector store index, saved as `Embeddings_chonkie`.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://your-repository-url.com/
    cd teno-bot-api
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a file named `.env` in the root directory and add the following variables. These are essential for connecting to the various services.

    ```env
    # Google AI Studio API Key
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

    # LangSmith for tracing and debugging (Optional)
    LANGSMITH_TRACING="true"
    LANGSMITH_API_KEY="YOUR_LANGSMITH_API_KEY"
    LANGSMITH_PROJECT="YOUR_LANGSMITH_PROJECT_NAME"

    # Supabase credentials for fetching user profiles
    SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
    SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"
    ```

### Running the Application

Once the setup is complete, you can run the local server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoint

### POST `/chat`

This is the main endpoint for interacting with the chatbot.

* **Method**: `POST`
* **Authentication**: `Bearer Token`
    ```
    Authorization: Bearer YOUR_AUTH_TOKEN
    ```

* **Request Body**:
    ```json
    {
      "session_id": "some-unique-session-id",
      "message": "Hello, I'm feeling a bit down today.",
      "reset": false
    }
    ```
    -   `session_id` (str): A unique identifier for the user's conversation.
    -   `message` (str): The user's message.
    -   `reset` (bool): If `true`, it ignores the fetched conversation history.

* **Success Response** (`200 OK`):
    ```json
    {
      "response": "I'm here to listen. It's okay to feel down sometimes. What's on your mind?"
    }
    ```

* **Error Responses**:
    -   `401 Unauthorized`: If the Bearer token is missing, invalid, or expired.
    -   `500 Internal Server Error`: If there's an issue fetching or saving data from external services.

## ☁️ Deployment

This project is configured for deployment on [Huggingface Spaces](https://huggingface.co/spaces/PetaniHandal/tenobot-api). Or you can access the image for this API in [Dockerhub](https://hub.docker.com/repository/docker/alfthrpy/tenobot-api)

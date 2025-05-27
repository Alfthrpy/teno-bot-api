from langchain.prompts import PromptTemplate

from langsmith import traceable
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
import torch
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langsmith import traceable
from langgraph.checkpoint.memory import MemorySaver
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
import logging
import time
from langchain_core.messages import HumanMessage, AIMessage
load_dotenv()

logging.basicConfig(
    level=logging.INFO,  # Atur level logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("Please set the GOOGLE_GENAI_API_KEY environment variable.")

os.environ["LANGSMITH_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT")





# Template lengkap untuk digunakan di app
system_prompt = SystemMessagePromptTemplate.from_template(
    """
Kamu adalah Teno, seorang konselor profesional yang penuh empati.
Tugasmu adalah menyimak dan memberikan respons yang singkat, manusiawi, dan langsung ke inti permasalahan.
Gunakan bahasa yang sederhana, suportif, dan jangan menggurui atau menghakimi.

kamu akan diberikan konteks dan riwayat percakapan sebelumnya. konteks tersebut adalah sekedar dokumen pendukung untuk memberikan respons, didapat dari hasil similarity search antara pertanyaan pengguna dengan dokumen yang ada, sehingga pengguna tidak tahu menahu soal konteks itu, jadi jangan pernah membicarakannya secara langsung.

selalu gunakan riwayat percakapan untuk membuat response yang baik, dan mengalir secara natural

Konteks :
{context}

Berikan respons yang hangat dan manusiawi.
Jika kamu merasa pengguna masih membutuhkan bantuan lebih lanjut atau situasinya belum jelas, kamu boleh menutup dengan ajakan untuk berbagi lebih lanjut.
Kalau tidak, cukup akhiri dengan pernyataan suportif tanpa perlu mengulang ajakan.
""".strip()
)

prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template(
        """
{question}
        """.strip()
    )
])



llm = init_chat_model(
    "gemini-2.0-flash",
    model_provider="google_genai",
    api_key=api_key
  )

# Load SBERT model dan pastikan menggunakan GPU jika tersedia
device = 'cuda' if torch.cuda.is_available() else 'cpu'
sbert_model = model = SentenceTransformer('naufalihsan/indonesian-sbert-large')
sbert_model = sbert_model.to(device)  # Pindahkan model ke GPU (jika ada)

# Custom embeddings class for SBERT
class SBERTEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Menggunakan model SBERT untuk menghasilkan embeddings
        embeddings = sbert_model.encode(texts, convert_to_tensor=True, show_progress_bar=True)
        embeddings = embeddings.to(device)  # Pindahkan embeddings ke GPU (jika ada)
        return embeddings.cpu().numpy().tolist()  # Pindahkan kembali ke CPU untuk konversi

    def embed_query(self, query: str) -> list[float]:
        # Menghasilkan embedding untuk query
        embedding = sbert_model.encode(query, convert_to_tensor=True)
        embedding = embedding.to(device)  # Pindahkan embedding ke GPU (jika ada)
        return embedding.cpu().numpy().tolist()  # Pindahkan kembali ke CPU untuk konversi

# Inisialisasi embeddings SBERT dan FAISS vector store
sbert_embeddings = SBERTEmbeddings()

def serialize_context(context_list):
    serialized = ""
    for idx, doc in enumerate(context_list, start=1):
        serialized += f"[Dokumen {idx}]\nJudul: {doc['BAB']}\nIsi: {doc['isi']}\n\n"
    return serialized


vector_store = FAISS.load_local("Embeddings_chonkie", sbert_embeddings, allow_dangerous_deserialization=True)

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    history: List[str]

def is_greeting(state: State) -> bool:
    greetings = ["hi", "hello", "hey", "halo"]
    return any(greet in state["question"].lower() for greet in greetings)


def retrieve(state: State):
    t1 = time.perf_counter()
    if is_greeting(state):
        return {"context": []}

    history = state.get("history", [])
    # Ambil 4 message terakhir (paling baru di awal)
    recent_context_texts = []
    for message in history[:4]:
        if isinstance(message, (HumanMessage, AIMessage)):
            recent_context_texts.append(message.content)

    recent_context = " ".join(recent_context_texts)

    enhanced_query = f"{recent_context} {state['question']}".strip()
    retrieved_docs = vector_store.similarity_search(enhanced_query, k=2)
    t2 = time.perf_counter()
    logging.info(f"Retrieved {len(retrieved_docs)} documents in {t2 - t1:.2f} seconds for query: {enhanced_query}")
    return {"context": retrieved_docs}

def generate(state: State):
    t1 = time.perf_counter()
    docs_content = [
        {
            "BAB": doc.metadata.get("bab", "Tidak diketahui"),
            "isi": doc.page_content
        }
        for doc in state["context"]
    ]
    serialized_context = serialize_context(docs_content)

    history = state.get("history", [])

    # Invoke prompt, langsung passing history (tanpa join text)
    messages = prompt.invoke({
        "history": history,
        "question": state["question"],
        "context": serialized_context
    })

    response = llm.invoke(messages)
    t2 = time.perf_counter()
    logging.info(f"Generated response in {t2 - t1:.2f} seconds for question: {state['question']}")

    # Salin history lama
    new_history = history.copy()

    # Tambahkan HumanMessage dan AIMessage ke awal
    new_history.insert(0, AIMessage(content=response.content))
    new_history.insert(0, HumanMessage(content=state["question"]))

    # Potong maksimal 3 pairs (6 items)
    MAX_HISTORY_PAIRS = 3
    if len(new_history) > MAX_HISTORY_PAIRS * 2:
        new_history = new_history[:MAX_HISTORY_PAIRS * 2]

    return {
        "answer": response.content,
        "history": new_history
    }


# Compile graph
graph_builder = StateGraph(State)
graph_builder.add_edge(START, "retrieve")
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)
graph_builder.add_edge("retrieve", "generate")

memory = MemorySaver()
app = graph_builder.compile(checkpointer=memory)
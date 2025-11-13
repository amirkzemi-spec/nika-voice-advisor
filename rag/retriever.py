import os
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# ----------------------------------------------------
# 🔐 Setup
# ----------------------------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INDEX_PATH = "rag/nika_index.faiss"
TEXT_PATH = "data/processed/all_knowledge.txt"

# Load FAISS index
if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
    print("✅ FAISS index loaded.")
else:
    index = None
    print("⚠️ No FAISS index found — RAG will rely on GPT reasoning.")

# Load text data (aligned with FAISS index vectors)
if os.path.exists(TEXT_PATH):
    with open(TEXT_PATH, "r", encoding="utf-8") as f:
        all_texts = [line.strip() for line in f.readlines() if line.strip()]
else:
    all_texts = []
    print("⚠️ No processed text file found — context retrieval disabled.")


# ----------------------------------------------------
# 🧭 Intent-based keyword bias
# ----------------------------------------------------
intent_bias = {
    "student_visa": "study visa university admission requirements tuition scholarship residence permit ",
    "startup_visa": "startup visa Netherlands IND RVO facilitator innovation business plan entrepreneur ",
    "visitor_visa": "tourist visa visitor visa UK cost requirements duration embassy appointment ",
    "freelancer_visa": "work permit freelancer self-employed business visa contract registration ",
    "residence_permit": "residence permit renewal extension permanent stay Netherlands EU card ",
    "family_reunion": "family reunification spouse dependent children application visa ",
    "embassy_docs": "embassy document submission appointment biometrics passport upload ",
}


# ----------------------------------------------------
# 🧠 Helper: Generate embedding
# ----------------------------------------------------
def get_embedding(text: str):
    """Convert text into an embedding vector."""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=[text],
    )
    return np.array(response.data[0].embedding, dtype="float32")


# ----------------------------------------------------
# 🔍 Context Retrieval
# ----------------------------------------------------
def get_context_for_query(query: str, intent: str = "unknown", k: int = 3):
    """
    Retrieve the top-k relevant text chunks using FAISS,
    with biasing based on detected intent.
    Falls back to GPT reasoning when no index or results exist.
    """
    if not index or not all_texts:
        print("⚠️ No FAISS index or text data — returning minimal context.")
        return f"No structured data found. The user asked: {query}"

    # Apply bias keywords depending on the detected intent
    bias = intent_bias.get(intent, "")
    combined_query = (bias + " " + query).strip()

    # Get embedding and search FAISS index
    vector = get_embedding(combined_query)
    D, I = index.search(np.array([vector]), k)

    # Collect matched text chunks
    results = [all_texts[i] for i in I[0] if i < len(all_texts)]

    if not results:
        print(f"⚠️ No RAG matches found for '{intent}' — GPT will reason freely.")
        return f"No direct matches found. The user asked: {query}"

    print(f"🧩 Retrieved {len(results)} chunks for intent '{intent}'")
    return "\n\n".join(results)

import os
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_texts(texts):
    """Ensure all inputs are clean strings"""
    return [str(t).strip() for t in texts if str(t).strip()]

def embed_texts(texts):
    """Generate embeddings using OpenAI Embeddings API"""
    texts = clean_texts(texts)
    if not texts:
        raise ValueError("No valid text chunks to embed.")
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts  # must be a list of strings
    )
    return [np.array(e.embedding, dtype="float32") for e in response.data]

def build_index(texts, save_path="rag/nika_index.faiss"):
    """Create FAISS index from text list"""
    texts = clean_texts(texts)
    vectors = embed_texts(texts)
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors))
    faiss.write_index(index, save_path)
    print(f"✅ Index built with {len(vectors)} entries")

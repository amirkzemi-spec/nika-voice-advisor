# nika_voice_ai/scripts/sync_rag_from_db.py

import json
import numpy as np
from pathlib import Path
from nika_voice_ai.utils.openai_client import client
import faiss

# -------------------------------------------------------
# Paths
# -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_JSON = PROJECT_ROOT / "data" / "db" / "records.json"
CHUNK_DIR = PROJECT_ROOT / "data" / "chunks"

OUTPUT_FAISS = PROJECT_ROOT / "rag" / "nika_index.faiss"
OUTPUT_TXT = PROJECT_ROOT / "data" / "processed" / "all_knowledge.txt"

OUTPUT_FAISS.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_TXT.parent.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------
# Embedding Helper
# -------------------------------------------------------
async def embed(texts: list[str]):
    """Generate embeddings from OpenAI safely."""
    if not texts:
        return []

    # OpenAI requires strict list[str]
    cleaned = [str(t).strip() for t in texts if isinstance(t, str) and t.strip()]

    if not cleaned:
        print("⚠️ No valid text entries to embed.")
        return []

    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=cleaned
    )

    return [item.embedding for item in response.data]


# -------------------------------------------------------
# Load Chunked Text
# -------------------------------------------------------
def load_chunks() -> list[str]:
    texts = []

    if not CHUNK_DIR.exists():
        print("⚠️ No chunk directory found:", CHUNK_DIR)
        return []

    for folder in CHUNK_DIR.iterdir():
        if not folder.is_dir():
            continue

        for file in folder.glob("*.txt"):
            try:
                content = file.read_text(encoding="utf-8", errors="ignore").strip()
                if content:
                    texts.append(content)
            except Exception as e:
                print(f"❌ Error reading chunk {file}: {e}")

    return texts


# -------------------------------------------------------
# Load DB JSON Records
# -------------------------------------------------------
def load_database_records() -> list[str]:
    if not DB_JSON.exists():
        return []

    try:
        data = json.loads(DB_JSON.read_text())
        return [d.get("text", "").strip() for d in data if isinstance(d, dict)]
    except Exception as e:
        print("❌ JSON load error:", e)
        return []


# -------------------------------------------------------
# Save Plaintext Debug Dump
# -------------------------------------------------------
def save_plaintext(texts: list[str]):
    merged = "\n\n".join(texts)
    OUTPUT_TXT.write_text(merged, encoding="utf-8")


# -------------------------------------------------------
# Main FAISS Builder
# -------------------------------------------------------
def run():
    import asyncio

    print("🧠 Loading text & DB records...")

    db_records = load_database_records()
    chunks = load_chunks()

    # Combine & clean
    all_texts = [t for t in (db_records + chunks) if isinstance(t, str) and t.strip()]

    print(f"📦 Total data entries: {len(all_texts)}")

    if not all_texts:
        print("⚠️ No data found — FAISS index not updated.")
        return

    async def build():
        print("🔍 Generating embeddings...")
        vectors = await embed(all_texts)

        if not vectors:
            print("❌ No embeddings returned — aborting.")
            return

        dim = len(vectors[0])
        index = faiss.IndexFlatL2(dim)

        index.add(np.array(vectors).astype("float32"))

        faiss.write_index(index, str(OUTPUT_FAISS))
        save_plaintext(all_texts)

        print("📦 FAISS index saved:", OUTPUT_FAISS)
        print("🗂️  Text dump saved:", OUTPUT_TXT)

    asyncio.run(build())


if __name__ == "__main__":
    run()

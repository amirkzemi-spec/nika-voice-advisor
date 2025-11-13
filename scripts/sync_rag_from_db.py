import os
import sys
import sqlite3
import faiss
import numpy as np
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------
# 🧭 Path setup (to import properly)
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# -----------------------------
# 🔐 Environment setup
# -----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# 📦 Paths
# -----------------------------
DB_PATH = ROOT_DIR / "db" / "nika_data.db"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
RAW_MERGED_TXT = PROCESSED_DIR / "all_knowledge_from_raw.txt"
FINAL_MERGED_TXT = PROCESSED_DIR / "all_knowledge.txt"
INDEX_PATH = ROOT_DIR / "rag" / "nika_index.faiss"

# -----------------------------
# 🧠 Helper: Get embedding
# -----------------------------
def get_embedding(text: str) -> np.ndarray:
    """Generate a text embedding vector."""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=[text]
    )
    return np.array(response.data[0].embedding, dtype="float32")

# -----------------------------
# 🧱 Build unified dataset
# -----------------------------
def build_unified_dataset():
    entries = []

    # 1️⃣ Add DB entries
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT country, visa_type, requirements, eligibility, duration, fee, benefits
            FROM visa_programs
        """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            text = " | ".join([str(x) for x in row if x])
            entries.append(text)
        print(f"✅ Loaded {len(rows)} records from database.")

    else:
        print("⚠️ Database not found — skipping DB part.")

    # 2️⃣ Add processed raw knowledge
    if RAW_MERGED_TXT.exists():
        raw_text = RAW_MERGED_TXT.read_text(encoding="utf-8").strip()
        paragraphs = [p.strip() for p in raw_text.split("\n") if len(p.strip()) > 50]
        entries.extend(paragraphs)
        print(f"✅ Loaded {len(paragraphs)} paragraphs from processed documents.")
    else:
        print("⚠️ No processed text file found — skipping document part.")

    # Deduplicate entries
    entries = list(dict.fromkeys(entries))
    print(f"📚 Total combined entries: {len(entries)}")
    return entries

# -----------------------------
# 🔄 Build FAISS index
# -----------------------------
def sync_rag_unified():
    all_entries = build_unified_dataset()
    if not all_entries:
        print("❌ No data found to index.")
        return

    vectors = []
    print(f"🔍 Generating {len(all_entries)} embeddings...")
    for text in all_entries:
        emb = get_embedding(text)
        vectors.append(emb)

    # Build FAISS index
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors))

    # Save FAISS index
    os.makedirs(INDEX_PATH.parent, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))

    # Save merged text
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    FINAL_MERGED_TXT.write_text("\n".join(all_entries), encoding="utf-8")

    print(f"✅ Unified FAISS index built successfully!")
    print(f"📦 Index saved to: {INDEX_PATH}")
    print(f"🗂️  Text data saved to: {FINAL_MERGED_TXT}")

# -----------------------------
# 🚀 Run script
# -----------------------------
if __name__ == "__main__":
    sync_rag_unified()

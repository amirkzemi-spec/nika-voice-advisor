import json
import sqlite3
import hashlib
import sys
from pathlib import Path

# -----------------------------
# 🧭 Path setup (fix import issue)
# -----------------------------
# Add project root to sys.path so "db" package can be imported correctly
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# -----------------------------
# 📦 Internal import (now works)
# -----------------------------
from db.models import DB_PATH  # noqa: E402

# -----------------------------
# 📄 Config
# -----------------------------
DATA_FILE = ROOT_DIR / "data" / "visa_data.json"

# -----------------------------
# 🧮 Helper functions
# -----------------------------
def get_hash(record):
    """Generate a unique hash to avoid duplicates."""
    key = (record.get("country", "") + record.get("visa_type", "")).lower()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


# -----------------------------
# 💾 Importer Logic
# -----------------------------
def import_json_to_db():
    if not DATA_FILE.exists():
        print(f"❌ {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    added, skipped = 0, 0

    for item in data:
        h = get_hash(item)
        cur.execute(
            "SELECT id FROM visa_programs WHERE country=? AND visa_type=?",
            (item.get("country"), item.get("visa_type")),
        )
        exists = cur.fetchone()

        if exists:
            print(f"⚠️ Skipping duplicate: {item.get('visa_type')} - {item.get('country')}")
            skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO visa_programs
            (country, visa_type, requirements, eligibility, duration, fee, benefits,
             application_link, source_url, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("country"),
                item.get("visa_type"),
                item.get("requirements"),
                item.get("eligibility"),
                item.get("duration"),
                item.get("fee"),
                item.get("benefits"),
                item.get("application_link"),
                item.get("source_url"),
                item.get("last_updated"),
            ),
        )
        print(f"✅ Added: {item.get('visa_type')} ({item.get('country')})")
        added += 1

    conn.commit()
    conn.close()
    print(f"🎯 Import completed successfully. Added: {added}, Skipped: {skipped}")


# -----------------------------
# 🚀 Run script
# -----------------------------
if __name__ == "__main__":
    import_json_to_db()
# -----------------------------
# 🔁 Auto-trigger RAG rebuild
# -----------------------------
import subprocess

def auto_sync_rag():
    """Automatically rebuild FAISS index after new DB imports."""
    try:
        print("\n⚙️  Updating unified RAG index ...")
        subprocess.run(
            ["python", "scripts/sync_rag_from_db.py"],
            check=True
        )
        print("✅ RAG index refreshed successfully.\n")
    except Exception as e:
        print(f"❌ Auto-sync failed: {e}")

# Run sync after import
if __name__ == "__main__":
    import_json_to_db()
    auto_sync_rag()

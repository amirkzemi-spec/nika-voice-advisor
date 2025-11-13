import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "nika_data.db"

def reset_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Drop old table if exists
    cur.execute("DROP TABLE IF EXISTS visa_programs")

    # Recreate with the new columns
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visa_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            visa_type TEXT,
            requirements TEXT,
            eligibility TEXT,
            duration TEXT,
            fee TEXT,
            benefits TEXT,
            application_link TEXT,
            source_url TEXT,
            last_updated TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ visa_programs table recreated successfully.")

if __name__ == "__main__":
    reset_schema()

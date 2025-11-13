import os
import json
import csv
import re
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/processed/all_knowledge_from_raw.txt")

def normalize_text(t):
    """Clean whitespace and punctuation"""
    t = re.sub(r"\s+", " ", str(t).strip())
    return t

# 🧩 Handlers for different file types
def process_json(file):
    data = json.load(open(file))
    chunks = []
    for entry in data:
        text = "\n".join([f"{k.capitalize()}: {v}" for k, v in entry.items() if v])
        chunks.append(text)
    return chunks

def process_txt(file):
    return [normalize_text(open(file).read())]

def process_csv(file):
    chunks = []
    with open(file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = "\n".join([f"{k.capitalize()}: {v}" for k, v in row.items() if v])
            chunks.append(text)
    return chunks

# 🧠 Auto-detect and process all supported files
def gather_all_data():
    os.makedirs(OUT_FILE.parent, exist_ok=True)
    all_chunks = []

    for file in RAW_DIR.glob("*"):
        if file.suffix == ".json":
            print(f"📦 Processing JSON: {file.name}")
            all_chunks.extend(process_json(file))
        elif file.suffix == ".txt":
            print(f"📄 Processing TXT: {file.name}")
            all_chunks.extend(process_txt(file))
        elif file.suffix == ".csv":
            print(f"🧾 Processing CSV: {file.name}")
            all_chunks.extend(process_csv(file))
        else:
            print(f"⚠️ Unsupported file type: {file.name}")

    # Save combined data
    if all_chunks:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n---\n".join([normalize_text(c) for c in all_chunks]))
        print(f"✅ Combined dataset saved to {OUT_FILE}")
    else:
        print("⚠️ No valid data sources found in data/raw/")

    # Sanity check
    sanity_check(OUT_FILE)

def sanity_check(file):
    data = open(file).read().split('---')
    non_empty = [t for t in data if t.strip()]
    print(f"🔍 Found {len(non_empty)} valid text chunks.")
    if len(non_empty) == 0:
        print("⚠️ File is empty — check your source files!")

if __name__ == "__main__":
    gather_all_data()

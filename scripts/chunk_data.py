# nika_voice_ai/scripts/chunk_data.py

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHUNK_DIR = PROJECT_ROOT / "data" / "chunks"
CHUNK_DIR.mkdir(parents=True, exist_ok=True)


def chunk_text(text: str, max_len=700):
    """Split text into paragraphs & chunks."""
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 20]

    chunks = []
    buffer = ""

    for p in paragraphs:
        if len(buffer) + len(p) < max_len:
            buffer += p + "\n"
        else:
            chunks.append(buffer.strip())
            buffer = p + "\n"

    if buffer.strip():
        chunks.append(buffer.strip())

    return chunks


def run():
    print("📚 Chunking data...")

    total_chunks = 0

    for country_folder in PROCESSED_DIR.iterdir():
        if not country_folder.is_dir():
            continue

        out_dir = CHUNK_DIR / country_folder.name
        out_dir.mkdir(exist_ok=True)

        for path in country_folder.glob("*.txt"):
            text = path.read_text(encoding="utf-8", errors="ignore")

            chunks = chunk_text(text)
            total_chunks += len(chunks)

            for i, chunk in enumerate(chunks):
                out_file = out_dir / f"{path.stem}_chunk{i}.txt"
                out_file.write_text(chunk, encoding="utf-8")

    print(f"📚 Total chunks created: {total_chunks}")


if __name__ == "__main__":
    run()

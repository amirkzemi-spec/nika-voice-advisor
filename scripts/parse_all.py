# nika_voice_ai/scripts/parse_all.py

import os
from pathlib import Path
from langdetect import detect
from nika_voice_ai.scripts.pdf_to_text import pdf_to_text
from nika_voice_ai.scripts.clean_text import clean_text

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _parse_txt_file(path: Path, out_dir: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        text = clean_text(text)

        try:
            lang = detect(text[:500])
        except:
            lang = "unknown"

        out_file = out_dir / f"{path.stem}_{lang}.txt"
        out_file.write_text(text, encoding="utf-8")

        print(f"📄 Parsed TXT → {out_file}")

    except Exception as e:
        print("❌ TXT parse error:", e)


def _parse_pdf_file(path: Path, out_dir: Path):
    try:
        text = pdf_to_text(str(path))
        text = clean_text(text)

        try:
            lang = detect(text[:500])
        except:
            lang = "unknown"

        out_file = out_dir / f"{path.stem}_{lang}.txt"
        out_file.write_text(text, encoding="utf-8")

        print(f"📄 Parsed PDF → {out_file}")

    except Exception as e:
        print("❌ PDF parse error:", e)


def run():
    print("🧹 Parsing TXT & PDF files...")

    for country_folder in RAW_DIR.iterdir():
        if not country_folder.is_dir():
            continue

        out_dir = PROCESSED_DIR / country_folder.name
        out_dir.mkdir(exist_ok=True)

        for path in country_folder.rglob("*"):
            if path.suffix.lower() == ".txt":
                _parse_txt_file(path, out_dir)
            elif path.suffix.lower() == ".pdf":
                _parse_pdf_file(path, out_dir)


if __name__ == "__main__":
    run()

import fitz
from pathlib import Path

def pdf_to_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    text = ""
    for page in doc:
        text += page.get_text()
    return text

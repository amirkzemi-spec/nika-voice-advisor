import fitz  # PyMuPDF
import docx
from pathlib import Path

def pdf_to_text(pdf_path, out_path=None):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    out_path = out_path or pdf_path.replace(".pdf", ".txt")
    Path(out_path).write_text(text)
    print(f"📘 Extracted {pdf_path} → {out_path}")

def docx_to_text(docx_path, out_path=None):
    doc = docx.Document(docx_path)
    text = "\n".join(p.text for p in doc.paragraphs)
    out_path = out_path or docx_path.replace(".docx", ".txt")
    Path(out_path).write_text(text)
    print(f"📄 Extracted {docx_path} → {out_path}")
if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 1:
        # process specific files passed as arguments
        for file in sys.argv[1:]:
            path = Path(file)
            if path.suffix.lower() == ".pdf":
                pdf_to_text(str(path))
            elif path.suffix.lower() == ".docx":
                docx_to_text(str(path))
    else:
        # process all PDFs and DOCXs in data/raw
        raw_dir = Path("data/raw")
        for file in raw_dir.glob("*"):
            if file.suffix.lower() == ".pdf":
                pdf_to_text(str(file))
            elif file.suffix.lower() == ".docx":
                docx_to_text(str(file))
import subprocess

def auto_sync_rag():
    try:
        print("\n⚙️  Updating unified RAG index after document parsing ...")
        subprocess.run(
            ["python", "scripts/sync_rag_from_db.py"],
            check=True
        )
        print("✅ Unified RAG index updated.\n")
    except Exception as e:
        print(f"❌ Auto-sync after parsing failed: {e}")

if __name__ == "__main__":
    # existing logic (parse, build, etc.)
    auto_sync_rag()

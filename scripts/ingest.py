# nika_voice_ai/scripts/ingest.py

from .scrape_urls import run as scrape_urls_run
from .parse_all import run as parse_all_run
from .chunk_data import run as chunk_data_run
from .sync_rag_from_db import run as sync_rag_run

def main():
    print("\n🔄 [1/4] Scraping URLs…")
    scrape_urls_run()

    print("\n🧹 [2/4] Parsing PDFs/TXT…")
    parse_all_run()

    print("\n📚 [3/4] Chunking data…")
    chunk_data_run()

    print("\n🧠 [4/4] Updating FAISS index…")
    sync_rag_run()

    print("\n🎉 DONE — RAG index fully updated!")

if __name__ == "__main__":
    main()

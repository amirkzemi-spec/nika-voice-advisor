# nika_voice_ai/scripts/scrape_urls.py

import os
import hashlib
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ---------------------------------------------------------
# ROOT-SAFE PATHS (works whether run as script or module)
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
HASH_FILE = PROJECT_ROOT / "data" / ".hashes"

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Load duplicate hashes (text fingerprint)
# Also track seen URLs to avoid crawling same pages
# ---------------------------------------------------------
if HASH_FILE.exists():
    SEEN_HASHES = set(HASH_FILE.read_text().splitlines())
else:
    SEEN_HASHES = set()

SEEN_URLS = set()


def save_hash(h):
    with open(HASH_FILE, "a") as f:
        f.write(h + "\n")


def get_hash(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_urls(path: Path):
    """Read a .txt file containing URLs."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip().startswith("http")]


def scrape_recursive(url, out_folder: Path, depth=1, max_depth=1):
    """Light recursive scraper that stays within the same domain."""
    if depth > max_depth:
        return

    if url in SEEN_URLS:
        return
    SEEN_URLS.add(url)

    try:
        print(f"🔍 Scraping {url}")

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")

        # hash check to prevent duplicates
        content_hash = get_hash(text)
        if content_hash in SEEN_HASHES:
            print("⚠️ Duplicate → skipped")
            return

        save_hash(content_hash)

        # sanitize filename
        file_name = (
            url.replace("https://", "")
               .replace("http://", "")
               .replace("/", "_")
               .replace("?", "_")
               .replace("=", "_")
        )[:140]

        out_path = out_folder / f"{file_name}.txt"
        out_path.write_text(text, encoding="utf-8")

        print(f"✅ Saved: {out_path}")

        # --------------------------------------
        # Crawl sub-links (ONLY within same site)
        # --------------------------------------
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        for tag in soup.find_all("a", href=True):
            href = tag["href"]

            # skip page fragments
            if href.startswith("#"):
                continue

            # build absolute URL
            if href.startswith("http"):
                next_url = href
            else:
                next_url = urljoin(base, href)

            # only crawl within same domain
            if base not in next_url:
                continue

            scrape_recursive(next_url, out_folder, depth + 1, max_depth)

    except Exception as e:
        print("❌ Scraper error:", e)


def run():
    """Entry point for ingestion."""
    print("\n🔍 Loading link files...")
    txt_files = RAW_DIR.glob("*.txt")

    for file in txt_files:
        country = file.stem.lower()
        print(f"\n🌍 Country detected: {country}")

        out_folder = RAW_DIR / country
        out_folder.mkdir(exist_ok=True)

        urls = extract_urls(file)
        print(f"📌 Found {len(urls)} urls")

        for url in urls:
            scrape_recursive(url, out_folder)


if __name__ == "__main__":
    run()

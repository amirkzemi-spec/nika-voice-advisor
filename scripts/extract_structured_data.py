import os
import sys
import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import subprocess

# -----------------------------
# 🧭 Path setup
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# -----------------------------
# 🔐 Load environment
# -----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# 📁 Paths
# -----------------------------
LINKS_FILE = ROOT_DIR / "data" / "raw" / "links.txt"
OUTPUT_JSON = ROOT_DIR / "data" / "visa_data.json"

# -----------------------------
# ⚙️ Helper: scrape and clean
# -----------------------------
def scrape_text_from_url(url: str) -> str:
    """Download and clean visible text from a webpage."""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        clean = "\n".join(line.strip() for line in text.splitlines() if len(line.strip()) > 0)
        return clean[:15000]  # limit for token safety
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return ""

# -----------------------------
# 🧠 Extract structured data via GPT
# -----------------------------
def extract_structured_data(url: str, text: str) -> dict:
    """Ask GPT to summarize webpage content into structured visa fields."""
    prompt = f"""
You are a precise immigration data extractor.

Read the following visa-related webpage text and output a *strict JSON object only*,
with no explanation or extra text.

Required fields:
[country, visa_type, requirements, eligibility, duration, fee, benefits,
 application_link, source_url, last_updated].

If information is missing, leave the field as an empty string ("").
Do not include Markdown, code fences, or commentary.
Output valid JSON only.

Source URL: {url}

Text (truncated to 15k chars):
{text[:15000]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You extract visa data for a database. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content.strip()

        # -----------------------------
        # 🧩 Attempt to fix common non-JSON cases
        # -----------------------------
        # Remove leading or trailing ```json ... ```
        if content.startswith("```"):
            content = content.split("```")[1]
        if content.strip().startswith("json"):
            content = content.split("json", 1)[-1]

        # Try to locate first { ... } block
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end + 1]

        data = json.loads(content)
        data["source_url"] = url
        data["last_updated"] = time.strftime("%Y-%m-%d")
        return data

    except Exception as e:
        print(f"❌ GPT extraction failed for {url}: {e}")
        return {}

# -----------------------------
# 📦 Main process
# -----------------------------
def main():
    if not LINKS_FILE.exists():
        print(f"❌ {LINKS_FILE} not found. Add your URLs there.")
        return

    urls = [u.strip() for u in LINKS_FILE.read_text().splitlines() if u.strip()]
    print(f"🌐 Found {len(urls)} links to process.")

    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 🕸️ Processing: {url}")
        text = scrape_text_from_url(url)
        if not text:
            continue
        record = extract_structured_data(url, text)
        if record:
            results.append(record)
        time.sleep(2)  # small delay to avoid rate limits

    if not results:
        print("⚠️ No structured data extracted.")
        return

    OUTPUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Saved {len(results)} structured records to {OUTPUT_JSON}")

    # -----------------------------
    # 🔁 Auto-import & sync RAG
    # -----------------------------
    try:
        print("\n⚙️  Importing data into DB and rebuilding RAG...")
        subprocess.run(["python", "scripts/import_json_to_db.py"], check=True)
        print("✅ Data imported and unified index updated successfully.")
    except Exception as e:
        print(f"❌ Auto-import failed: {e}")


# -----------------------------
# 🚀 Run
# -----------------------------
if __name__ == "__main__":
    main()

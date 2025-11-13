import requests
from bs4 import BeautifulSoup
from pathlib import Path

def scrape_page(url, outfile="data/raw/web_scraped.txt"):
    r = requests.get(url, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    text = " ".join(p.get_text() for p in soup.find_all(["p", "li"]))
    Path(outfile).write_text(text)
    print(f"✅ Scraped {url} → {outfile}")

# Example use
scrape_page("https://ind.nl/en/startup", "data/raw/nl_startup_visa.txt")

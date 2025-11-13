# utils/openai_client.py
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "":
    raise ValueError("❌ OPENAI_API_KEY not found! Please add it to your .env file.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
# --- Debug logger (inline version of utils.dev_console) ---
import os
from datetime import datetime
import colorama
colorama.init(autoreset=True)

DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
COLORS = {
    "info": colorama.Fore.CYAN,
    "ok": colorama.Fore.GREEN,
    "warn": colorama.Fore.YELLOW,
    "error": colorama.Fore.RED,
    "reset": colorama.Style.RESET_ALL,
}

def log(event: str, msg: str = "", level: str = "info"):
    if not DEBUG and level not in ["error", "warn"]:
        return
    color = COLORS.get(level, COLORS["info"])
    now = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{now}] {event}:{COLORS['reset']} {msg}")

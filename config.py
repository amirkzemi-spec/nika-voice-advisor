# config.py
import os
from dotenv import load_dotenv

# Load variables from .env (local) or Railway environment
load_dotenv()

# ---------------------------------------
# 🔐 Supabase Credentials
# ---------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_REDIRECT = os.getenv(
    "SUPABASE_REDIRECT",
    "http://127.0.0.1:8000/auth/supabase/callback"
)

# ---------------------------------------
# 🤖 OpenAI Credentials
# ---------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------------------------------------
# 🛠️ Debug Mode
# ---------------------------------------
DEBUG = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")

# ---------------------------------------
# 🌍 Environment (local or production)
# ---------------------------------------
ENV = os.getenv("ENV", "local").lower()

# Optional: Raise errors if critical env vars are missing
if not SUPABASE_URL:
    raise RuntimeError("❌ Missing SUPABASE_URL in environment")

if not SUPABASE_KEY:
    raise RuntimeError("❌ Missing SUPABASE_KEY in environment")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ Missing OPENAI_API_KEY in environment")

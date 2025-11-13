import os
import uuid
from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from aiocache import Cache
from fastapi.responses import RedirectResponse
from datetime import date
from auth.routes_supabase import supabase

# ==========================================================
# 🚀 Initialize FastAPI App FIRST
# ==========================================================
app = FastAPI(title="🎙️ Nika Visa AI – Walkie Talkie Mode")

# ==========================================================
# ✅ Internal modules (based on your structure)
# ==========================================================
from utils.session_manager import update_session
from utils.openai_client import client, log
from utils.nika_logic import gpt_reply
from utils.audio_converter import convert_to_wav
from utils.speech_to_text import transcribe_audio
from utils.text_to_speech import speak_reply
from db.schema import SessionLocal, Base
from auth.routes_basic import router as basic_auth_router
from auth.routes_profile import router as profile_router
from auth.routes_supabase import router as supabase_router
from auth.routes_upgrade import router as upgrade_router


# ==========================================================
# 🔌 Routers
# ==========================================================
app.include_router(basic_auth_router)
app.include_router(profile_router)
app.include_router(supabase_router)
app.include_router(upgrade_router)



# ==========================================================
# 🌐 Middleware & Templates
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

Cache.DEFAULT_CACHE = Cache.MEMORY
cache = Cache()


# ==========================================================
# 🏠 Home
# ==========================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Landing page showing login status."""
    user_email = request.cookies.get("user_email")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user_email": user_email}
    )



# ==========================================================
# 🌍 Middleware and static setup
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧩 Template + Static setup
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 💾 Simple in-memory cache (sessions, limits, etc.)
Cache.DEFAULT_CACHE = Cache.MEMORY
cache = Cache()

# ==========================================================
# 🔐 Include Authentication Routers
# ==========================================================
app.include_router(basic_auth_router)
app.include_router(profile_router)
app.include_router(supabase_router)
# ==========================================================
# 🏠 Home Page
# ==========================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user_email = request.cookies.get("user_email")
    return templates.TemplateResponse("index.html", {"request": request, "user_email": user_email})





# ==========================================================
# 🎤 Voice Upload Endpoint (with Tier System)
# ==========================================================
@app.post("/voice-upload")
async def voice_upload(request: Request, file: UploadFile):
    try:
        user_email = request.cookies.get("user_email")

        # --------------------------------------------------
        # 1️⃣ Guest users (not logged in)
        # --------------------------------------------------
        if not user_email:
            key = f"anon_{request.client.host}"
            count = await cache.get(key) or 0
            count += 1
            await cache.set(key, count)
            if count > 5:   # ← increased demo limit from 2 → 5
                return JSONResponse(
                    {"error": "demo_limit", "message": "Free guest limit reached. Please log in."},
                    status_code=401,
                )

        # --------------------------------------------------
        # 2️⃣ Logged-in users → check tier & daily usage
        # --------------------------------------------------
        else:
            profile = supabase.table("profiles").select("*").eq("email", user_email).execute()

            if not profile.data:
                # Auto-create profile on first login
                supabase.table("profiles").insert({
                    "email": user_email,
                    "tier": "free",
                    "turns_today": 0,
                    "last_used": str(date.today())
                }).execute()
                tier, turns, last_used = "free", 0, str(date.today())
            else:
                p = profile.data[0]
                tier = p.get("tier", "free")
                turns = p.get("turns_today", 0)
                last_used = p.get("last_used")

            # Reset counter if it's a new day
            today = str(date.today())
            if last_used != today:
                turns = 0
                supabase.table("profiles").update(
                    {"turns_today": 0, "last_used": today}
                ).eq("email", user_email).execute()

            # Define per-tier daily limits
            LIMITS = {"free": 10, "pro": 25}
            limit = LIMITS.get(tier, 10)

            # Check usage
            if turns >= limit:
             return JSONResponse({
                "error": "limit_reached",
                "tier": tier,
                "message": (
                    "You've reached your daily limit of free voice questions. "
                    "Please come back tomorrow or upgrade to premium for unlimited access."
                )
            }, status_code=401)


            # Increment turn count
            supabase.table("profiles").update(
                {"turns_today": turns + 1}
            ).eq("email", user_email).execute()

        # --------------------------------------------------
        # ✅ Continue with STT → GPT → TTS logic
        # --------------------------------------------------
        log("🎧 Upload", f"Received file: {file.filename}")
        input_bytes = await file.read()

        wav_path = convert_to_wav(input_bytes, mime_type=file.content_type)
        log("🔊 Convert", f"Created WAV: {wav_path}")

        text = await transcribe_audio(wav_path)
        if not text.strip():
            return JSONResponse({"error": "No speech detected"}, status_code=400)
        log("🗣️ Transcribed", text)

        reply = await gpt_reply(text)
        if not reply.strip():
            reply = "I'm sorry, I couldn't generate a response right now."
        log("🤖 GPT Reply", reply)

        os.makedirs("static/uploads", exist_ok=True)
        tts_name = f"reply_{uuid.uuid4().hex}.ogg"
        tts_path = os.path.join("static", "uploads", tts_name)
        await speak_reply(reply, tts_path)
        log("🎙️ TTS", f"Saved {tts_path}")

        return JSONResponse({"audio_url": f"/{tts_path}"})

    except Exception as e:
        log("❌ Error", str(e), level="error")
        return JSONResponse({"error": str(e)}, status_code=500)

    finally:
        if "wav_path" in locals() and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass


# ==========================================================
# 📂 Serve TTS Files
# ==========================================================
@app.get("/static/uploads/{filename}")
async def get_audio(filename: str):
    """Return generated TTS files."""
    path = os.path.join("static", "uploads", filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "file not found"}, status_code=404)
    return FileResponse(path, media_type="audio/ogg")


# ==========================================================
# 🧪 Ping Test
# ==========================================================
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Nika Visa Walkie-Talkie active ✅"}


# ==========================================================
# 🔐 Login + Logout
# ==========================================================
@app.post("/login")
async def login(request: Request, name: str = Form(...), email: str = Form(...)):
    print("🟢 /login called with:", name, email)  # 🔍 debug line

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ New user created: {user.name} ({user.email})")
    else:
        print(f"👋 Returning user: {user.name} ({user.email})")

    # set cookie so user stays logged in
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_email", value=user_email, httponly=True)
    return response

# ==========================================================
# 🔐 Upgrade to premium
# ==========================================================
@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("user_email")
    return response

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page(request: Request):
    return templates.TemplateResponse("upgrade.html", {"request": request})

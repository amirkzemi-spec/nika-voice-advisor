from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse
from datetime import date
import os
import uuid

from auth.routes_supabase import supabase
from aiocache import Cache
from utils.openai_client import log
from utils.audio_converter import convert_to_wav
from utils.speech_to_text import transcribe_audio
from utils.text_to_speech import speak_reply
from utils.nika_logic import gpt_reply

cache = Cache()
router = APIRouter()

@router.post("/voice-upload")
async def voice_upload(request: Request, file: UploadFile):
    try:
        user_email = request.cookies.get("user_email")

        # 1️⃣ Guest restrictions
        if not user_email:
            key = f"anon_{request.client.host}"
            count = await cache.get(key) or 0
            count += 1
            await cache.set(key, count)
            if count > 5:
                return JSONResponse(
                    {"error": "demo_limit", "message": "Free guest limit reached. Please log in."},
                    status_code=401
                )

        # 2️⃣ Logged in → tier logic
        else:
            profile = supabase.table("profiles").select("*").eq("email", user_email).execute()
            if not profile.data:
                supabase.table("profiles").insert({
                    "email": user_email,
                    "tier": "free",
                    "turns_today": 0,
                    "last_used": str(date.today())
                }).execute()
                tier = "free"
                turns = 0
            else:
                p = profile.data[0]
                tier = p.get("tier", "free")
                turns = p.get("turns_today", 0)
                last_used = p.get("last_used")

            today = str(date.today())
            if last_used != today:
                turns = 0
                supabase.table("profiles").update(
                    {"turns_today": 0, "last_used": today}
                ).eq("email", user_email).execute()

            LIMITS = {"free": 10, "pro": 25}
            if turns >= LIMITS.get(tier, 10):
                return JSONResponse(
                    {"error": "limit_reached", "tier": tier,
                     "message": "Daily limit reached. Upgrade for more."},
                    status_code=401
                )

            supabase.table("profiles").update(
                {"turns_today": turns + 1}
            ).eq("email", user_email).execute()

        # Processing STT → GPT → TTS
        input_bytes = await file.read()
        wav_path = convert_to_wav(input_bytes, mime_type=file.content_type)

        text = await transcribe_audio(wav_path)
        reply = await gpt_reply(text)

        os.makedirs("static/uploads", exist_ok=True)
        tts_name = f"reply_{uuid.uuid4().hex}.ogg"
        tts_path = os.path.join("static", "uploads", tts_name)
        await speak_reply(reply, tts_path)

        return JSONResponse({"audio_url": f"/{tts_path}"})

    finally:
        if "wav_path" in locals() and os.path.exists(wav_path):
            os.remove(wav_path)

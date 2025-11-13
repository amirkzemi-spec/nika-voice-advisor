import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

# -----------------------------
# 🔐 Environment + client setup
# -----------------------------
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------------
# 🔊 Async text-to-speech helper
# -----------------------------
async def speak_reply(
    text: str,
    out_path: str,
    user_id: str = "web_user",
    voice: str = "alloy",
):
    """
    Convert text into spoken voice and save it to `out_path`.
    Compatible with FastAPI streaming loop.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 🧼 Sanitize text
    if not text or not text.strip():
        print("⚠️ Empty text input — skipping TTS.")
        with open(out_path, "wb") as f:
            f.write(b"")
        return out_path

    # Truncate long replies
    if len(text) > 800:
        text = text[:800] + " ..."

    # 🌐 Detect Persian/Farsi text
    is_farsi = any("\u0600" <= ch <= "\u06FF" for ch in text)
    if is_farsi:
        print("🌙 Detected Farsi text → using 'verse' voice.")
        voice = "verse"
    else:
        voice = "alloy"

    try:
        # 🎤 Generate audio
        response = await client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
        )

        # 📝 Save bytes
        audio_bytes = getattr(response, "data", None)
        if audio_bytes is None and hasattr(response, "read"):
            audio_bytes = response.read()

        if not audio_bytes:
            raise ValueError("Empty audio response from TTS model.")

        with open(out_path, "wb") as f:
            f.write(audio_bytes)

        print(f"🎧 Voice reply saved to: {out_path}")
        return out_path

    except Exception as e:
        print(f"❌ TTS generation failed: {e}")
        # Fallback empty file so system never breaks
        with open(out_path, "wb") as f:
            f.write(b"")
        return out_path


# -----------------------------
# 🧪 Test mode (optional)
# -----------------------------
if __name__ == "__main__":
    async def _test():
        print("🎙️ Testing TTS synthesis...")
        test_path = "static/uploads/test_tts.ogg"
        result = await speak_reply("سلام، من نیکا هستم. خوش آمدید!", test_path)
        print("✅ Generated:", result)

    asyncio.run(_test())

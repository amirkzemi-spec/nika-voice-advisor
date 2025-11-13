import os
import asyncio
import aiofiles
import soundfile as sf
import numpy as np
import tempfile
import subprocess
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------------------------------------------------
# 🎙️  Fast Whisper Transcription
# ----------------------------------------------------
async def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe a voice file using OpenAI Whisper (optimized).
    - Downsamples to 12 kHz mono for faster upload
    - Retries once if Whisper fails
    """
    if not os.path.exists(audio_path):
        print(f"⚠️ File not found: {audio_path}")
        return ""

    # 🧩 Pre-process for speed
    tmp_path = os.path.join(tempfile.gettempdir(), "nika_fast.wav")
    try:
        # Convert to 12 kHz mono
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-y", "-i", audio_path,
            "-ac", "1", "-ar", "12000",
            tmp_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Skip empty / micro clips
        if os.path.getsize(tmp_path) < 4000:
            print("⚠️ Very short clip skipped.")
            return ""

        async with aiofiles.open(tmp_path, "rb") as f:
            audio_bytes = await f.read()

        # 🧠 Whisper API (async)
        for attempt in range(2):
            try:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", audio_bytes, "audio/wav")
                )
                text = response.text.strip()
                if text:
                    print(f"🗣️ Transcribed: {text}")
                    return text
            except Exception as e:
                print(f"⚠️ Whisper attempt {attempt+1} failed: {e}")
                await asyncio.sleep(0.5)
                continue

        return ""
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# ----------------------------------------------------
# 🧩  Streaming version (optional)
# ----------------------------------------------------
async def transcribe_in_chunks(audio_path: str, chunk_ms: int = 5000):
    """
    Split long recordings into ~5 s chunks and stream partial transcriptions.
    """
    data, sr = sf.read(audio_path, dtype="float32")
    frame_len = int(sr * (chunk_ms / 1000))
    total_frames = len(data)

    for i in range(0, total_frames, frame_len):
        segment = data[i:i+frame_len]
        if np.mean(np.abs(segment)) < 0.01:  # skip near-silence
            continue
        tmp = os.path.join(tempfile.gettempdir(), f"chunk_{i}.wav")
        sf.write(tmp, segment, sr)
        text = await transcribe_audio(tmp)
        if text:
            yield text
        os.remove(tmp)

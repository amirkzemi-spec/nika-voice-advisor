import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from rag.retriever import get_context_for_query  # ✅ RAG
from utils.session_memory import summarize_memory, save_session, get_session  # 🧠 Memory integration
from utils.advisor_logic import detect_mode, get_or_ask_profile  # 🎯 Advisory logic

# -------------------------------------------
# 🧩 Simple internal logger (no dependencies)
# -------------------------------------------
def log(tag: str, message: str, level: str = "info"):
    color_map = {
        "info": "\033[94m", "warn": "\033[93m",
        "error": "\033[91m", "success": "\033[92m"
    }
    color = color_map.get(level, "\033[0m")
    reset = "\033[0m"
    print(f"{color}[{tag}] {message}{reset}")

# 🔐 Load API key and init OpenAI client
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# ----------------------------------------------------
# 🎯 Generate advisory recommendation
# ----------------------------------------------------
async def generate_advice(user_id: str, is_farsi: bool = True) -> str:
    """
    Once profile is complete → generate personalized recommendations
    based on user's answers.
    """
    from utils.session_memory import get_session
    session = await get_session(user_id)
    profile = session.get("profile", {})

    profile_summary = "\n".join([f"{k}: {v}" for k, v in profile.items()])
    log("🧩 Advisory", f"Generating recommendations for: {profile_summary}")

    prompt = f"""
User profile:
{profile_summary}

You are Nika, an expert immigration advisor.
Recommend the top 2 countries and study programs suitable for this user.
Be practical and concise (max 80 words).
Respond in the same language as the user.
    """

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Expert immigration advisor"},
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=0.6,
            max_tokens=150,
        )

        reply = completion.choices[0].message.content.strip()
        await save_session(user_id, "advisory_recommendation", "profile_complete", reply)
        log("🤖 Advisor Reply", reply)
        return reply

    except Exception as e:
        log("❌ Advisory", f"Error generating recommendation: {e}", level="error")
        return (
            "خطایی در تولید پیشنهاد رخ داد. لطفاً دوباره تلاش کنید."
            if is_farsi else
            "There was an error generating your recommendation. Please try again."
        )

# ----------------------------------------------------
# 🧠 GPT reply with Mode Switch + RAG + Memory + Smart Tone
# ----------------------------------------------------
async def gpt_reply(user_text: str, user_id: str = "web_user", intent: str = "unknown") -> str:
    """
    Handles two flows:
    1️⃣ General Q&A mode (RAG + memory)
    2️⃣ Advisory mode (profile guidance and personalized suggestions)
    Adds human-like tone and summarization for multi-question inputs.
    """

    if not user_text or not user_text.strip():
        return "⚠️ من صدای واضحی نشنیدم. لطفاً دوباره بگو."

    # 🈯 Detect Farsi vs English
    is_farsi = any("\u0600" <= ch <= "\u06FF" for ch in user_text)

    # 🧊 Detect first-time user
    session = await get_session(user_id)
    if not session:
        log("👋 Welcome", "First interaction detected — sending greeting.")
        await save_session(user_id, "intro", "first_greeting", "done")
        return (
            "Hi there! Welcome to Nika Visa AI Assistant. "
            "Would you like to ask general immigration questions, "
            "or would you like me to give personalized advice based on your background?"
            if not is_farsi
            else
            "سلام! خوش اومدی به نیکا ویزا. "
            "می‌خوای سوالات عمومی مهاجرتی بپرسی یا بر اساس شرایط خودت برات مشاوره شخصی‌سازی‌شده بدم؟"
        )

    # 🎯 Detect user mode (advisory vs general)
    mode = await detect_mode(user_text, user_id)
    log("🧭 Mode", f"Active mode: {mode}")

    # 👤 If advisory mode → collect or complete profile
    if mode == "advisory":
        profile, question = await get_or_ask_profile(user_id)
        if question:
            return question  # Ask next missing field before GPT
        else:
            log("🧾 Profile", f"Profile complete: {profile}")

    # 🧠 Retrieve past memory summary
    try:
        memory_context = await summarize_memory(user_id)
    except Exception:
        memory_context = ""

    # 🔍 Retrieve RAG context
    try:
        context = get_context_for_query(user_text)
    except Exception:
        context = ""

    # 💬 Smart handling for multi-question messages
    question_count = user_text.count("?") + user_text.count("؟")
    too_many_questions = question_count >= 3

    if too_many_questions:
        log("🧮 Query", f"Detected {question_count} questions — summarizing mode.")
        if is_farsi:
            polite_intro = (
                "چند سؤال خیلی خوب پرسیدی! اجازه بده از مهم‌ترینش شروع کنیم "
                "و بعد دونه‌دونه بقیه رو هم بررسی کنیم."
            )
            pre_prompt = (
                "کاربر چند سؤال پشت سر هم پرسیده است. "
                "با لحنی دوستانه و مشاور‌گونه فقط به مهم‌ترین سؤالات پاسخ بده "
                "و بگو که در ادامه می‌توانی بقیه را هم توضیح دهی."
            )
        else:
            polite_intro = (
                "That’s a lot of great questions! Let’s start with the most important one, "
                "and I’ll help you go through the rest next."
            )
            pre_prompt = (
                "The user asked several questions in one message. "
                "You are a calm, friendly immigration consultant — acknowledge it politely, "
                "answer the key questions first, and mention you can cover others next."
            )
    else:
        pre_prompt = ""
        polite_intro = ""

    # 🧩 Build system prompt (consultant tone)
    system_prompt = (
        "تو نیکا هستی، یک دستیار مهاجرت دقیق و طبیعی. "
        "پاسخ‌هایت باید کوتاه، صوتی‌پسند و مودبانه باشند. "
        f"{pre_prompt}\n{context}\n{memory_context}"
        if is_farsi else
        "You are Nika, a friendly and accurate visa & immigration consultant. "
        "Keep replies short, warm, and natural for spoken output. "
        f"{pre_prompt}\nUse this info if relevant:\n{context}\n{memory_context}"
    )

    # 🧠 Dynamic length control
    max_len = 180 if too_many_questions else 100

    # 🚀 Generate GPT reply
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text.strip()},
            ],
            temperature=0.45,
            max_tokens=max_len,
        )
        reply = completion.choices[0].message.content.strip()

        if too_many_questions:
            reply = f"{polite_intro}\n{reply}"

        log("🤖 GPT Reply", reply)
        await save_session(user_id, intent, user_text, reply)
        return reply

    except Exception as e:
        log("❌ GPT", f"Error: {e}", level="error")
        return (
            "متاسفم، خطایی رخ داد. لطفاً دوباره تلاش کن."
            if is_farsi else
            "Sorry, something went wrong. Please try again."
        )

# ----------------------------------------------------
# 🔊 Quick GPT → TTS helper
# ----------------------------------------------------
async def text_to_voice(user_text: str, out_path: str):
    from utils.text_to_speech import speak_reply
    reply = await gpt_reply(user_text)
    await speak_reply(reply, out_path)
    return out_path

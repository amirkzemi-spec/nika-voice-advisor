# utils/advisor_logic.py
import re
from utils.session_memory import get_session, save_session

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

# ---------------------------------------------------
# 🎯 Detect mode: advisory vs general Q&A
# ---------------------------------------------------
async def detect_mode(user_text: str, user_id: str):
    """
    Detect if user wants general questions (qa) or personalized advice (advisory).
    Remembers user’s mode inside the session.
    """
    text = user_text.lower()
    session = await get_session(user_id)
    mode = "qa"

    # Check existing mode
    if session and "mode" in session:
        mode = session["mode"]

    # Detect user intent
    if any(k in text for k in ["advice", "recommend", "personal", "based on me", "help me choose"]):
        mode = "advisory"
    elif any(k in text for k in ["general", "question", "info", "information"]):
        mode = "qa"

    # Persist mode
    await save_session(user_id, "mode", "set_mode", {"mode": mode})
    log("🧭 Mode", f"User mode set to: {mode}")
    return mode

# ---------------------------------------------------
# 🧠 Get or ask for user’s immigration profile
# ---------------------------------------------------
async def get_or_ask_profile(user_id: str):
    """
    Retrieve user's immigration profile or ask missing questions.
    Example fields: age, degree, English level, marital status, budget.
    """
    session = await get_session(user_id)
    profile = {}

    # ✅ Safely extract profile
    if session and isinstance(session, dict):
        profile = session.get("profile", {})
    else:
        profile = {}

    # Identify missing fields
    fields = ["age", "latest_degree", "english_level", "marital_status", "budget"]
    missing = [f for f in fields if not profile.get(f)]

    # Ask next missing question
    if missing:
        field = missing[0]
        question_map = {
            "age": {"en": "What is your age?", "fa": "چند سالته؟"},
            "latest_degree": {"en": "What is your latest degree or education level?", "fa": "آخرین مدرک یا مقطع تحصیلی‌ات چیه؟"},
            "english_level": {"en": "What is your English level (IELTS, TOEFL, etc.)?", "fa": "سطح زبان انگلیسی‌ات چقدره؟ (مثل آیلتس یا تافل)"},
            "marital_status": {"en": "Are you single or married?", "fa": "مجردی یا متأهل؟"},
            "budget": {"en": "What is your approximate study or visa budget in euros?", "fa": "بودجه‌ی تقریبی‌ات برای تحصیل یا ویزا چقدره؟ (به یورو)"}
        }

        question = question_map[field]["fa" if user_id.startswith("fa_") else "en"]

        # Save last asked field
        session = session or {}
        session["last_field"] = field
        await save_session(user_id, "advisory", "ask_profile", session)
        log("🧾 Profile", f"Asking for {field}")
        return profile, question

    # ✅ All fields filled
    return profile, None

# ---------------------------------------------------
# 🧱 Update user's profile with new answer
# ---------------------------------------------------
async def update_profile(user_id: str, user_text: str):
    """Extract and store a user's profile field based on last question."""
    session = await get_session(user_id)
    if not session:
        session = {}

    profile = session.get("profile", {})
    last_field = session.get("last_field")

    if not last_field:
        log("⚠️ Profile", "No last_field found — cannot update.")
        return profile, None

    text_lower = user_text.lower()
    val = user_text.strip()

    # Simple rules for field mapping
    if last_field == "age":
        num = re.findall(r"\d+", text_lower)
        profile["age"] = num[0] if num else val
    elif last_field == "latest_degree":
        profile["latest_degree"] = val
    elif last_field == "english_level":
        profile["english_level"] = val
    elif last_field == "marital_status":
        profile["marital_status"] = val
    elif last_field == "budget":
        profile["budget"] = val

    # Save progress
    session["profile"] = profile
    session["last_field"] = None
    await save_session(user_id, "advisory", "update_profile", session)

    log("🧾 Profile", f"Updated {last_field}: {val}")
    return profile, None

# ---------------------------------------------------
# 🎯 Suggest study options once profile complete
# ---------------------------------------------------
async def suggest_study_options(profile: dict):
    """Generate high-level suggestions based on filled profile."""
    age = profile.get("age", "")
    degree = profile.get("latest_degree", "").lower()
    budget = profile.get("budget", "")
    english = profile.get("english_level", "")
    marital = profile.get("marital_status", "")

    # ✅ Basic heuristic (expandable)
    if "high school" in degree or "diploma" in degree:
        suggestion = (
            "Since you have a high school diploma, bachelor programs in Europe or Canada "
            "are a good fit. Focus on IELTS 6.0+ and a budget around €10,000–€15,000 per year."
        )
    elif "bachelor" in degree:
        suggestion = (
            "With a bachelor's degree, consider master's programs in Finland, Germany, or the Netherlands. "
            "They often offer low tuition and English-taught programs."
        )
    elif "master" in degree or "postgraduate" in degree:
        suggestion = (
            "With a master's background, you could apply for PhD or research visas in Europe or Canada."
        )
    else:
        suggestion = (
            "Once I know your degree and English level, I can suggest suitable countries and programs."
        )

    # 🧠 Add nuance based on budget or English
    if "ielts" in english.lower() or "toefl" in english.lower():
        suggestion += " Good! Your English preparation helps you qualify faster."
    if budget and any(b in budget for b in ["5000", "8000", "10000", "€"]):
        suggestion += " Your budget suggests affordable destinations like Finland or Poland."

    log("🎯 Suggestion", suggestion)
    return suggestion

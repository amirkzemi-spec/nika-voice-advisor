import re

def classify_intent(text: str) -> str:
    """Return high-level intent for user message (supports EN + FA)."""
    t = text.lower().strip()

    # ----------------------------
    # English Keywords
    # ----------------------------
    if any(word in t for word in ["startup", "founder", "entrepreneur", "innovative business"]):
        return "startup_visa"

    if any(word in t for word in ["student", "study", "university", "college", "msc", "phd", "education"]):
        return "student_visa"

    if any(word in t for word in ["tourist", "visit", "visitor", "holiday", "short stay", "travel"]):
        return "visitor_visa"

    if any(word in t for word in ["work", "job", "freelancer", "self-employed", "employment"]):
        return "freelancer_visa"

    if any(word in t for word in ["permanent", "residence", "pr", "citizenship", "immigrate"]):
        return "residence_permit"

    # ----------------------------
    # Persian / Farsi Keywords
    # ----------------------------
    if re.search(r"استارت.?آپ|کارآفرین|بیزینس نو", t):
        return "startup_visa"

    if re.search(r"دانشجو|تحصیل|دانشگاه|مدرسه|ویزا.?تحصیلی", t):
        return "student_visa"

    if re.search(r"توریستی|ویزای.?بازدید|مسافرت|دیدار|توریست", t):
        return "visitor_visa"

    if re.search(r"کار|ویزای.?کار|فریلنسر|خویش.?فرما", t):
        return "freelancer_visa"

    if re.search(r"اقامت|مهاجرت|شهروندی", t):
        return "residence_permit"

    return "unknown"

# nika_voice_ai/scripts/clean_text.py

import re

def clean_text(text: str) -> str:
    """
    Normalize whitespace, remove HTML artifacts, fix spacing,
    and produce a clean version of extracted text for chunking.
    """

    if not text:
        return ""

    # Remove script/style tags (if any HTML remains)
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.MULTILINE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.MULTILINE)

    # Remove HTML entities
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"&amp;?", "&", text)
    text = re.sub(r"&quot;?", '"', text)

    # Remove multiple spaces / newlines
    text = re.sub(r"\s+", " ", text)

    # Restore paragraph structure (better for chunking)
    text = text.replace(". ", ".\n")

    # Trim
    return text.strip()

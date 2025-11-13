import time
from aiocache import Cache

# 🧠 Simple in-memory short-term memory (auto expires after 30 min)
Cache.DEFAULT_CACHE = Cache.MEMORY
cache = Cache()
SESSION_TTL = 1800  # 30 minutes
MAX_MEMORY_TURNS = 3  # keep last 3 user–assistant pairs


async def save_session(user_id: str, intent: str, last_query: str, last_reply: str):
    """
    Save the latest user interaction.
    If previous sessions exist, append and trim old entries.
    """
    session = await cache.get(user_id) or {"history": []}

    # Append new turn
    session["history"].append({
        "intent": intent,
        "query": last_query,
        "reply": last_reply,
        "timestamp": time.time(),
    })

    # Keep only the last N turns
    if len(session["history"]) > MAX_MEMORY_TURNS:
        session["history"] = session["history"][-MAX_MEMORY_TURNS:]

    await cache.set(user_id, session, ttl=SESSION_TTL)
    print(f"💾 Memory updated for {user_id} | turns={len(session['history'])}")


async def get_session(user_id: str):
    """
    Retrieve recent memory for user (list of last N turns).
    """
    session = await cache.get(user_id)
    if not session:
        return None

    # Auto-refresh TTL to keep active users longer
    await cache.set(user_id, session, ttl=SESSION_TTL)
    return session


async def summarize_memory(user_id: str):
    """
    Convert past interactions into a text summary for context injection.
    """
    session = await cache.get(user_id)
    if not session or not session.get("history"):
        return ""

    parts = []
    for turn in session["history"]:
        q = turn.get("query", "")
        a = turn.get("reply", "")
        parts.append(f"User asked: {q}\nAssistant replied: {a}")

    summary = "\n\n".join(parts)
    return f"[Conversation Memory]\n{summary}"


async def clear_session(user_id: str):
    """Manually clear user memory."""
    await cache.delete(user_id)
    print(f"🧹 Cleared memory for {user_id}")

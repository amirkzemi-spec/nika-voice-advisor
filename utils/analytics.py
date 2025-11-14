from fastapi import Request
from supabase import create_client
import os

async def track_visit(request: Request, status="guest"):
    try:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        ip = request.client.host
        ua = request.headers.get("user-agent", "unknown")

        supabase.table("visitors").insert({
            "ip_address": ip,
            "user_agent": ua,
            "status": status
        }).execute()

    except Exception as e:
        print("Tracking error:", e)

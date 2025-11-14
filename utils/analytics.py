# utils/analytics.py

from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# ---------------------------------------
# 🔌 Create Supabase client (shared)
# ---------------------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------
# 📊 Track Visitor
# ---------------------------------------
async def track_visit(request, status="guest"):
    try:
        ip = request.client.host
        ua = request.headers.get("user-agent", "unknown")

        supabase.table("visitors").insert({
            "ip_address": ip,
            "user_agent": ua,
            "status": status
        }).execute()

    except Exception as e:
        print("Tracking error:", e)

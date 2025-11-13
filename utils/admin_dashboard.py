import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 🔹 Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # 🧩 Fetch all user profiles
    response = supabase.table("profiles").select("*").execute()
    data = response.data or []

    # 🧮 Basic stats
    total_users = len(data)
    free_users = len([u for u in data if u.get("tier") == "free"])
    pro_users = len([u for u in data if u.get("tier") == "pro"])

    # 🔹 Fetch visitor stats
    visitors_response = supabase.table("visitors").select("*").execute()
    visitors = visitors_response.data or []
    bounced = len([v for v in visitors if v.get("status") == "guest"])
    converted = len([v for v in visitors if v.get("status") == "converted"])

    # Optional: sort by last_used (latest first)
    data.sort(key=lambda u: u.get("last_used") or "", reverse=True)

    # 🧠 Render dashboard
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "total_users": total_users,
            "free_users": free_users,
            "pro_users": pro_users,
            "users": data,
            "bounced": bounced,
            "converted": converted,
        },
    )

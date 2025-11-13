import os
import urllib.parse
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
from dotenv import load_dotenv

# --------------------------------------------------
# 🔐 Load environment variables
# --------------------------------------------------
load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------
# ⚙️ Supabase setup
# --------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_REDIRECT = os.getenv("SUPABASE_REDIRECT") or "http://127.0.0.1:8000/auth/supabase/callback"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Missing Supabase credentials in environment (.env)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --------------------------------------------------
# 🔗 1️⃣ Redirect to Supabase Google Auth
# --------------------------------------------------
@router.get("/auth/supabase/login")
async def supabase_login():
    redirect_url = (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider=google&redirect_to={SUPABASE_REDIRECT}"
    )
    print("🔗 Redirecting user to:", redirect_url)
    return RedirectResponse(url=redirect_url)


# --------------------------------------------------
# 🔁 2️⃣ Handle Supabase callback (OAuth)
# --------------------------------------------------
@router.get("/auth/supabase/callback")
async def supabase_callback(request: Request):
    """
    Handles Supabase OAuth redirect.
    If the token is missing (because Supabase returned it in the URL hash),
    serve a helper HTML to extract it client-side and reload.
    """
    url = str(request.url)
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    fragment = urllib.parse.parse_qs(parsed.fragment)
    all_params = {**query, **fragment}

    access_token = all_params.get("access_token", [None])[0]

    if not access_token:
        # Serve JS extractor if token came in URL fragment
        return templates.TemplateResponse("supabase_callback.html", {"request": request})

    try:
        user = supabase.auth.get_user(access_token)
        email = user.user.email if user and user.user else None
        if not email:
            return JSONResponse({"error": "No user email found"}, status_code=400)

        print(f"✅ Logged in via Google: {email}")
        response = RedirectResponse(url="/")
        response.set_cookie("user_email", email, httponly=True, samesite="lax")
        return response

    except Exception as e:
        print("❌ Auth error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# 🚪 3️⃣ Logout helper (clears cookie)
# --------------------------------------------------
@router.get("/auth/logout")
async def supabase_logout(request: Request):
    print("🧹 Logging out user:", request.cookies.get("user_email"))
    response = RedirectResponse(url="/")
    response.delete_cookie("user_email")
    return response

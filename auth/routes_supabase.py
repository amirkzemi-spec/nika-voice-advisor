# auth/routes_supabase.py

import urllib.parse
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_REDIRECT

# --------------------------------------------------
# 🔌 Create global Supabase client (importable everywhere)
# --------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------
# 🔗 Login Redirect
# --------------------------------------------------
@router.get("/auth/supabase/login")
async def supabase_login():
    redirect_url = (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider=google&redirect_to={SUPABASE_REDIRECT}"
    )
    print("🔗 Redirecting user:", redirect_url)
    return RedirectResponse(url=redirect_url)


# --------------------------------------------------
# 🔁 OAuth Callback
# --------------------------------------------------
@router.get("/auth/supabase/callback")
async def supabase_callback(request: Request):

    url = str(request.url)
    parsed = urllib.parse.urlparse(url)

    query = urllib.parse.parse_qs(parsed.query)
    fragment = urllib.parse.parse_qs(parsed.fragment)
    all_params = {**query, **fragment}

    access_token = all_params.get("access_token", [None])[0]

    if not access_token:
        return templates.TemplateResponse(
            "supabase_callback.html",
            {"request": request}
        )

    try:
        user = supabase.auth.get_user(access_token)
        email = user.user.email if user and user.user else None

        if not email:
            return JSONResponse({"error": "No user email found"}, status_code=400)

        print(f"✅ Google Login Success: {email}")

        response = RedirectResponse(url="/")
        response.set_cookie("user_email", email, httponly=True, samesite="lax")
        return response

    except Exception as e:
        print("❌ OAuth Error:", e)
        return JSONResponse({"error": str(e)}, 500)


# --------------------------------------------------
# 🚪 Logout
# --------------------------------------------------
@router.get("/auth/logout")
async def supabase_logout(request: Request):
    email = request.cookies.get("user_email")
    print("🧹 Logging out:", email)

    response = RedirectResponse(url="/")
    response.delete_cookie("user_email")
    return response

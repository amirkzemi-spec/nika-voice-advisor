# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ======================================
# Initialize App
# ======================================
app = FastAPI(title="🎙️ Nika Visa AI – Walkie Talkie Mode")

# ======================================
# CORS
# ======================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ⚠️ restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================
# Templates & Static
# ======================================
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ======================================
# Router Imports
# ======================================
from routes.home import router as home_router
from routes.voice import router as voice_router
from routes.static_files import router as static_router
from routes.system import router as system_router

from auth.routes_basic import router as basic_router
from auth.routes_profile import router as profile_router
from auth.routes_supabase import router as supabase_router
from auth.routes_upgrade import router as upgrade_router

from utils.admin_dashboard import router as admin_router

# ======================================
# Router Registration
# ======================================
app.include_router(home_router)
app.include_router(voice_router)
app.include_router(static_router)
app.include_router(system_router)

# ❌ Removed: analytics_router (it does not exist anymore)
# app.include_router(analytics_router)

app.include_router(basic_router)
app.include_router(profile_router)
app.include_router(supabase_router)
app.include_router(upgrade_router)
app.include_router(admin_router)

# ===========================================
# auth/routes_profile.py
# ===========================================
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from db.schema import SessionLocal, User

router = APIRouter(tags=["User Profile"])
templates = Jinja2Templates(directory="templates")


# ------------------------------------------
# Helper to get DB session
# ------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------
# Get current logged-in user
# ------------------------------------------
def get_current_user(request: Request, db):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


# ------------------------------------------
# View profile
# ------------------------------------------
@router.get("/profile", response_class=HTMLResponse)
async def view_profile(request: Request, db: SessionLocal = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    context = {
        "request": request,
        "user": user,
    }
    return templates.TemplateResponse("profile.html", context)


# ------------------------------------------
# Edit profile form
# ------------------------------------------
@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile(request: Request, db: SessionLocal = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    context = {"request": request, "user": user}
    return templates.TemplateResponse("profile_edit.html", context)


# ------------------------------------------
# Update profile
# ------------------------------------------
@router.post("/profile/update")
async def update_profile(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    db: SessionLocal = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    user.name = name
    user.email = email
    db.commit()
    db.refresh(user)
    print(f"✅ Profile updated: {user.name} ({user.email})")

    return RedirectResponse(url="/profile", status_code=302)

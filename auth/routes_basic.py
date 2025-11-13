# ===========================================
# auth/routes_basic.py
# ===========================================
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from db.schema import SessionLocal, User
from passlib.context import CryptContext
from datetime import datetime

router = APIRouter(tags=["Auth - Basic"])
templates = Jinja2Templates(directory="templates")

# 🔐 password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ------------------------------------------------
# helpers
# ------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed: str) -> bool:
    return pwd_context.verify(plain_password, hashed)


# ------------------------------------------------
# registration
# ------------------------------------------------
@router.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: SessionLocal = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return JSONResponse({"error": "Email already registered"}, status_code=400)

    new_user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        created_at=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_id", value=str(new_user.id), httponly=True)
    return response


# ------------------------------------------------
# login
# ------------------------------------------------
@router.post("/login/basic")
async def login_basic(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: SessionLocal = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password:
        return JSONResponse({"error": "User not found"}, status_code=404)

    if not verify_password(password, user.hashed_password):
        return JSONResponse({"error": "Invalid password"}, status_code=401)

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


# ------------------------------------------------
# logout
# ------------------------------------------------
@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("user_id")
    return response


# ------------------------------------------------
# forgot-password (optional)
# ------------------------------------------------
@router.post("/reset")
async def reset_password(
    email: str = Form(...),
    new_password: str = Form(...),
    db: SessionLocal = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return JSONResponse({"error": "Email not found"}, status_code=404)

    user.hashed_password = hash_password(new_password)
    db.commit()
    return JSONResponse({"message": "Password updated"})

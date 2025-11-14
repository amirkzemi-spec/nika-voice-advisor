# routes/home.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.analytics import track_visit

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    await track_visit(request)
    user_email = request.cookies.get("user_email")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user_email": user_email}
    )

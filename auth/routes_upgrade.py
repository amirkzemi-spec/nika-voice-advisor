from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page(request: Request):
    return templates.TemplateResponse("upgrade.html", {"request": request})

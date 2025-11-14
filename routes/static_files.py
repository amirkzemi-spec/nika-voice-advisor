from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
import os

router = APIRouter()

@router.get("/static/uploads/{filename}")
async def get_audio(filename: str):
    path = os.path.join("static", "uploads", filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "file not found"}, status_code=404)
    return FileResponse(path, media_type="audio/ogg")

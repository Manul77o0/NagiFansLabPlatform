from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()
INDEX_FILE = Path(__file__).resolve().parents[2] / "static" / "index.html"


@router.get("/", name="root")
async def root():
    return FileResponse(INDEX_FILE)

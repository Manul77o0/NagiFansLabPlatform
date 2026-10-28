from fastapi import APIRouter, Request
from app.common_libs.common import _get_session, _clear_session

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={418: {"description": "I'm a teapot"}},
)


# Session情報を使用する例
@router.get("/info")
async def session_info(request: Request):
    session: dict = _get_session(request)

    result = {
        "session_id": session["session_id"],
        "count": session["count"],
    }
    return result
# Sessionをクリアする例
@router.get("/clear")
async def clear_session(request: Request):
    _clear_session(request)
    return {"message": "Session cleared"}
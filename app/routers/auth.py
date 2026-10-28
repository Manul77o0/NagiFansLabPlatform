from typing import Annotated
from fastapi import APIRouter, Request, Form
from app.main import templates
from loguru import logger
from fastapi.responses import RedirectResponse
from app.common_libs.common import _get_session, _clear_session

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={418: {"description": "I'm a teapot"}},
)

dummy_user = [
    {
        "uid": 1,
        "username": "testuser",
        "password": "password123"
    }
]

@router.get("/login")
async def root(request: Request, ref_url: str | None = None, error: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"ref_url": ref_url, "error": error}
    )

@router.post("/login")
async def login(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()], ref_url: Annotated[str | None, Form()] = None):

    user = next((u for u in dummy_user if u["username"] == username and u["password"] == password), None)
    if not user:
        logger.warning(f"Failed login attempt for username: {username}")
        if ref_url:
            url = request.url_for("login").include_query_params(ref_url=ref_url, error="認証に失敗しました")
        else:
            url = request.url_for("login").include_query_params(error="認証に失敗しました")
        return RedirectResponse(url=url, status_code=303)

    session: dict = _get_session(request)
    session["user_name"] = user["username"]
    session["user_id"] = user["uid"]
    session["is_authenticated"] = True
    logger.info(f"User logged in: {session['user_id']}")

    if ref_url:
        return RedirectResponse(url=ref_url, status_code=303)
    return RedirectResponse(url=f"/", status_code=303)

@router.get("/register")
async def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )
@router.get("/logout")
async def logout(request: Request):
    session: dict = _get_session(request)
    logger.info(f"User logged out: {session['user_id']}")
    _clear_session(request)
    return RedirectResponse(url=f"/", status_code=303)

@router.get("/me")
async def me(request: Request):
    session: dict = _get_session(request)
    if not session.get("is_authenticated"):
        url = request.url_for("login").include_query_params(ref_url=str(request.url), error="認証が必要です")
        return RedirectResponse(url=url, status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="me.html",
        context={"session": session}
    )
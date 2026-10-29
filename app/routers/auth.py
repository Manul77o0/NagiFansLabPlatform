from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy import select

from app.common_libs.common import (
    _clear_session,
    _get_session,
    _init_session,
    get_password_hash,
    verify_password,
)
from app.database import AsyncSession, get_db
from app.main import templates
from app.models import User

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={418: {"description": "I'm a teapot"}},
)

@router.get("/login")
async def login(request: Request, error: str | None = None):
    ref_url = request.session.get("ref_url")
    error = request.session.get("error")
    session = await _init_session(request)
    if ref_url:
        session["ref_url"] = ref_url
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error}
    )

@router.post("/login")
async def login_post(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()], db: Annotated[AsyncSession, Depends(get_db)],):

    session: dict = await _get_session(request)
    result = await db.scalars(select(User).where(User.email == username+"@nagifans.cc"))
    user = result.first()
    if not user:
        verify_password(password)
        logger.warning(f"Failed login attempt for username: {username}")
        session["error"] = "認証に失敗しました"
        return RedirectResponse(url=request.url_for("login"), status_code=303)
    if not verify_password(password, user.password):
        logger.warning(f"Failed login attempt for username: {username}")
        session["error"] = "認証に失敗しました"
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    ref_url = request.session.get("ref_url")
    session = await _init_session(request)
    session["user_name"] = user.name
    session["user_id"] = user.id
    session["is_authenticated"] = True
    session["error"] = None
    logger.info(f"User logged in: {session['user_id']}")

    if ref_url:
        return RedirectResponse(url=ref_url, status_code=303)
    return RedirectResponse(url="/", status_code=303)

@router.get("/register")
async def register(request: Request):
    session: dict = await _get_session(request)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": None}
    )

@router.post("/register")
async def register_post(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()], db: Annotated[AsyncSession, Depends(get_db)]):
    hashed_password = get_password_hash(password)
    new_user = User(name=username, email=username+"@nagifans.cc", password=hashed_password)
    db.add(new_user)
    await db.commit()
    return RedirectResponse(url=request.url_for("login"), status_code=303)

@router.get("/logout")
async def logout(request: Request):
    session: dict = await _get_session(request)
    logger.info(f"User logged out: {session['user_id']}")
    _clear_session(request)
    return RedirectResponse(url="/", status_code=303)

@router.get("/me")
async def me(request: Request):
    session: dict = await _get_session(request)
    if not session.get("is_authenticated"):
        session["ref_url"] = str(request.url)
        session["error"] = "認証が必要です"
        return RedirectResponse(url=request.url_for("login"), status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="me.html",
        context={"session": session}
    )
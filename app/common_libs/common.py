import uuid

from fastapi import Request
from loguru import logger

from pwdlib import PasswordHash
from app.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

async def _init_session(request: Request):
    request.session.clear()
    request.session["session_id"] = str(uuid.uuid4())
    request.session["count"] = 0
    
    if request.session.get("is_authenticated") and request.session.get("user_id"):
        async with AsyncSessionLocal() as db:
            result = await db.scalars(select(User).where(User.id == request.session.get("user_id")))
            user = result.first()
        if user:
            request.session["user_name"] = user.name
    logger.debug(f"new session is: {request.session}")
    return request.session

async def _get_session(request: Request):
    if not request.session:
        await _init_session(request)
    request.session["count"] += 1
    logger.debug(f"session is: {request.session}")
    return request.session

def _clear_session(request: Request):
    logger.debug(f"session cleared: {request.session}")
    request.session.clear()


def verify_password(plain_password, hashed_password=DUMMY_HASH):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)
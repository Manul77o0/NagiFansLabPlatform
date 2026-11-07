from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from jwt.exceptions import InvalidTokenError
from loguru import logger
from sqlalchemy import select

from app.common.const import (
    ACCESS_TOKEN_COOKIE,
    ALGORITHM,
    COOKIE_SECURE,
    DOMAIN,
    DUMMY_HASH,
    SECRET_KEY,
    oauth2_scheme,
    password_hash,
)
from app.common.schema import TokenData, User, UserInDB
from app.database import AsyncSession, get_db
from app.models import SystemUser


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)

def get_resettoken(email: str, last_updated_at: datetime) -> str:
    payload = {
        "sub": email,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "type": "password_reset",
        "upd": last_updated_at.timestamp()
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(db: AsyncSession, username: str) -> UserInDB | None:
    result = await db.execute(
        select(SystemUser).where(
            SystemUser.email == f"{username}@{DOMAIN}",
            SystemUser.disabled == 0
        )
    )
    db_user = result.scalar_one_or_none()
    if db_user is None:
        return None

    return UserInDB(
        id=db_user.id,
        displayname=db_user.name,
        email=db_user.email,
        disabled=bool(db_user.disabled),
        level=db_user.level,
        hashed_password=db_user.password,
    )

async def get_user_uid(db: AsyncSession, id: int) -> UserInDB | None:
    result = await db.execute(
        select(SystemUser).where(
            SystemUser.id == id
        )
    )
    db_user = result.scalar_one_or_none()
    if db_user is None:
        return None

    return UserInDB(
        id=db_user.id,
        displayname=db_user.name,
        email=db_user.email,
        disabled=bool(db_user.disabled),
        level=db_user.level,
        hashed_password=db_user.password,
    )

async def get_all_user(db: AsyncSession) -> list[User]:
    result = await db.execute(
        select(SystemUser)
    )
    db_users = result.scalars().all()
    logger.debug(f"{db_users=}")
    
    return [
        User(
            id=db_user.id,
            displayname=db_user.name,
            email=db_user.email,
            disabled=bool(db_user.disabled),
            level=db_user.level,
        )
        for db_user in db_users
    ]


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> UserInDB | bool:
    user = await get_user(db, username)
    # logger.debug(f'{get_password_hash("password")}')
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    logger.info(f'User:{data["sub"]} Create Access Token.')
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_from_access_token(token: str, db: AsyncSession) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError as e:
        raise credentials_exception from e
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    access_token = token or request.cookies.get(ACCESS_TOKEN_COOKIE)
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await get_user_from_access_token(access_token, db)


async def get_optional_cookie_user(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if token is None:
        return None

    try:
        return await get_user_from_access_token(token, db)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_401_UNAUTHORIZED:
            raise
        response.delete_cookie(
            ACCESS_TOKEN_COOKIE,
            path="/",
            secure=COOKIE_SECURE,
            httponly=True,
            samesite="lax",
        )
        return None


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def check_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> bool:
    if current_user.level < 3:
        raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Enough Role",
                )
    return True
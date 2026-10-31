import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from loguru import logger
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlalchemy import select

from app.database import AsyncSession, get_db
from app.models import SystemUser

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")
ACCESS_TOKEN_COOKIE = "access_token"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

app = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str


class BrowserLogin(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


async def get_user(db: AsyncSession, username: str) -> UserInDB | None:
    result = await db.execute(
        select(SystemUser).where(
            SystemUser.email == f"{username}@nagifans.cc"
        )
    )
    db_user = result.scalar_one_or_none()
    if db_user is None:
        return None

    return UserInDB(
        username=username,
        email=db_user.email,
        disabled=bool(db_user.disabled),
        hashed_password=db_user.password,
    )


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> UserInDB | bool:
    user = await get_user(db, username)
    logger.debug(f'{get_password_hash("password")}')
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
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/session/login", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def login_for_browser_session(
    credentials: BrowserLogin,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    user = await authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


@app.post("/session/logout", include_in_schema=False)
async def logout_browser_session(response: Response) -> dict[str, bool]:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True}


@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
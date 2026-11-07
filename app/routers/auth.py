import os
from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.common.auth_func import (
    authenticate_user,
    check_admin,
    create_access_token,
    get_all_user,
    get_current_active_user,
    get_password_hash,
    get_resettoken,
    get_user,
    get_user_uid,
)
from app.common.const import (
    ACCESS_TOKEN_COOKIE,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    COOKIE_SECURE,
    DOMAIN,
    SECRET_KEY,
)
from app.common.email import send_email
from app.common.schema import (
    BrowserLogin,
    ResetPasswordRequest,
    Result,
    Token,
    Tools,
    UpdateUserLevelRequest,
    UpdateUserRequest,
    User,
)
from app.database import AsyncSession, get_db
from app.models import SystemUser

app = APIRouter()


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
        data={"sub": user.email.replace(f"@{DOMAIN}", "")}, expires_delta=access_token_expires
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
        data={"sub": user.email.replace(f"@{DOMAIN}", "")},
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
async def logout_browser_session(response: Response) -> Result:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )
    return Result(result="success")


@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@app.get("/users/me/tools/")
async def read_usable_tools(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    tools_list = [{"WireGuardTools": "/wg_tools"}]
    if current_user.level >= 3:
        tools_list.append({"UserManageTools": "/admin/users"})
    return Tools(tools=tools_list)


@app.get("/admin/users", dependencies=[Depends(check_admin)])
async def read_all_users(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> list[User]:
    return await get_all_user(db)

@app.post("/admin/user/register", dependencies=[Depends(check_admin)])
async def register_user(
    credentials: BrowserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Result:
    user = await get_user(db, credentials.username)
    if user is None:
        try:
            await db.execute(
                    insert(SystemUser).values(name=credentials.username, email=f"{credentials.username}@{DOMAIN}", password=get_password_hash(credentials.password), disabled=1).returning(SystemUser)
                )
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Insert Users Table Error -> {e}")
            await db.rollback()
            raise HTTPException(status_code=400, detail="Invalid username or password") from e
    else:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return Result(result="success")

@app.post("/admin/user/{user_id}/enable", dependencies=[Depends(check_admin)])
async def enable_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Result:
    user = await get_user_uid(db, user_id)
    if user is not None and user_id != current_user.id:
        try:
            await db.execute(
                    update(SystemUser).where(SystemUser.id==user_id).values(disabled=0).returning(SystemUser)
                )
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Update Users Table Error -> {e}")
            await db.rollback()
            raise
    else:
        raise HTTPException(status_code=400, detail="Invalid uid")
    return Result(result="success")

@app.post("/admin/user/{user_id}/disable", dependencies=[Depends(check_admin)])
async def disble_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Result:
    user = await get_user_uid(db, user_id)
    if user is not None and user_id != current_user.id:
        try:
            await db.execute(
                    update(SystemUser).where(SystemUser.id==user_id).values(disabled=1).returning(SystemUser)
                )
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Update Users Table Error -> {e}")
            await db.rollback()
            raise
    else:
        raise HTTPException(status_code=400, detail="Invalid uid")
    return Result(result="success")

@app.post("/admin/user/{user_id}/update", dependencies=[Depends(check_admin)])
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Result:
    user = await get_user_uid(db, user_id)
    if user is not None and user_id != current_user.id:
        try:
            await db.execute(
                    update(SystemUser).where(SystemUser.id==user_id).values(name=request.displayName).returning(SystemUser)
                )
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Update Users Table Error -> {e}")
            await db.rollback()
            raise
    else:
        raise HTTPException(status_code=400, detail="Invalid uid")
    return Result(result="success")

@app.post("/admin/user/{user_id}/level", dependencies=[Depends(check_admin)])
async def update_user_level(
    user_id: int,
    request: UpdateUserLevelRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    user = await get_user_uid(db, user_id)
    if user is None or user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Invalid uid")

    if user.level == 3 and request.level < 3 and not user.disabled:
        result = await db.execute(
            select(func.count()).select_from(SystemUser).where(
                SystemUser.level == 3,
                SystemUser.disabled == 0,
            )
        )
        if result.scalar_one() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="At least one active administrator must remain",
            )
    try:
        result = await db.execute(
            update(SystemUser)
            .where(SystemUser.id == user_id)
            .values(level=request.level)
            .returning(SystemUser)
        )
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning(f"Update Users Table Error -> {e}")
        await db.rollback()
        raise

    updated_user = result.scalar_one()
    return User(
        id=updated_user.id,
        displayname=updated_user.name,
        email=updated_user.email,
        disabled=bool(updated_user.disabled),
        level=updated_user.level,
    )

@app.post("/admin/user/{user_id}/reset", dependencies=[Depends(check_admin)])
async def reset_pw_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Result:
    user = await get_user_uid(db, user_id)
    if user is not None:
        try:
            result = await db.execute(
                    update(SystemUser).where(SystemUser.id==user_id).values(password=None).returning(SystemUser)
                )
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Update Users Table Error -> {e}")
            await db.rollback()
            raise
    else:
        raise HTTPException(status_code=400, detail="Invalid uid")
    add_user = result.scalar_one()
    token = get_resettoken(add_user.email, add_user.updated_at)
    await send_email([add_user.email], "パスワードリセット", f"下記URLからパスワードリセットを行ってください。(発行から30分間有効です)\n{ os.environ.get('EXTERNAL_URL')}/reset?token={token}")
    return Result(result="success")

@app.post("/reset", include_in_schema=False)
async def reset_password(request: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "password_reset":
            logger.warning("Invalid token type")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="無効なトークンです"
            )

        email = payload.get("sub")
        if email is None:
            logger.warning("Invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="無効なトークンです"
            )

    except jwt.ExpiredSignatureError as e:
        logger.warning("Expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なトークンです",
        ) from e
    except jwt.PyJWTError as e:
        logger.warning("Not Validate token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="無効なトークンです"
        ) from e

    try:
        new_password_hash = get_password_hash(request.new_password)
        result = await db.execute(
                update(SystemUser).where(SystemUser.email == email, SystemUser.updated_at == datetime.fromtimestamp(payload.get("upd"))).values(password=new_password_hash).returning(SystemUser)
            )
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning(f"Update Users Table Error -> {e}")
        await db.rollback()
        raise
    add_user = result.scalar_one_or_none()
    if add_user:
        return 
    else:
        logger.warning(f"Old UPDT Timestamp -> {datetime.fromtimestamp(payload.get("upd"))}")
        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="このトークンはすでに使用されています"
                )
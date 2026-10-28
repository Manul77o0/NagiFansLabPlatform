from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import datetime
import os
from dotenv import load_dotenv

# 共通系処理
load_dotenv()

_FASTAPI_SESSION_SECRET_KEY = os.environ.get("FASTAPI_SESSION_SECRET_KEY")
_FASTAPI_SESSION_TIMEOUT_MIN = os.environ.get("FASTAPI_SESSION_TIMEOUT_MIN")
if not _FASTAPI_SESSION_SECRET_KEY:
    raise ValueError("FASTAPI_SESSION_SECRET_KEY is not set in environment variables.")
try:
    _FASTAPI_SESSION_TIMEOUT_MIN = int(_FASTAPI_SESSION_TIMEOUT_MIN)
except (TypeError, ValueError):
    raise ValueError("FASTAPI_SESSION_TIMEOUT_MIN is not set or is not a valid integer.")

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=_FASTAPI_SESSION_SECRET_KEY ,
    max_age=(int)(datetime.timedelta(minutes=_FASTAPI_SESSION_TIMEOUT_MIN).total_seconds()),
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# エンドポイント追加したらここに記載
from app.routers import root, sessions, auth
app.include_router(root.router)
app.include_router(sessions.router)
app.include_router(auth.router)
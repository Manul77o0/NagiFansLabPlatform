import os

from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
DOMAIN = os.environ.get("DOMAIN")

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")
ACCESS_TOKEN_COOKIE = "access_token"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
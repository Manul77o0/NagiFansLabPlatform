from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class BrowserLogin(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    id: int
    displayname: str
    email: str | None = None
    level: int | None = 0
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str | None = None


class UpdateUserRequest(BaseModel):
    displayName: str


class UpdateUserLevelRequest(BaseModel):
    level: int = Field(strict=True, ge=1, le=3)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class Result(BaseModel):
    result: str

class Tools(BaseModel):
    tools: list
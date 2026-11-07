from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.database import AsyncSession, get_db
from typing import Annotated

class User(BaseModel):
    id: int
    displayname: str
    email: str | None = None
    level: int | None = 0
    disabled: bool | None = None

app = APIRouter(prefix="/wg_tools")

@app.get("/")
async def hello_world():
    return "hello"

@app.get("/global_settings")
async def get_global_settings(
    db: Annotated[AsyncSession, Depends(get_db)],):
    return "hello"
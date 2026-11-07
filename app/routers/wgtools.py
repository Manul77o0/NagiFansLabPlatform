from fastapi import APIRouter

app = APIRouter(prefix="/wg_tools")

@app.get("/")
async def hello_world():
    return "hello"
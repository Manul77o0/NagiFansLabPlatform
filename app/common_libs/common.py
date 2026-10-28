from fastapi import Request
import uuid
from loguru import logger

def _get_session(request: Request):
    if not request.session:
        request.session["session_id"] = str(uuid.uuid4())
        request.session["count"] = 0
        logger.debug(f"new session is: {request.session}")
    request.session["count"] += 1
    logger.debug(f"session is: {request.session}")
    return request.session

def _clear_session(request: Request):
    logger.debug(f"session cleared: {request.session}")
    request.session.clear()

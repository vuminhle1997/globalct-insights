from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from redis import Redis
from sqlmodel import Session
from starlette.requests import Request

from backend.dependencies import get_db_session, get_redis_client, logger
from backend.models.chat import Chat
from backend.routers.custom_router import APIRouter
from backend.utils import verify_session_and_get_user_id

router = APIRouter(
    prefix="/avatar",
    tags=["avatar"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{chat_id}")
async def get_avatar_of_chat(
    chat_id: str,
    request: Request,
    db_client: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
):
    db_chat = db_client.get(Chat, chat_id)

    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    user_id, _ = verify_session_and_get_user_id(request, redis_client)
    if db_chat.user_id != user_id:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to you")

    # Get avatar file path and return file response
    return FileResponse(db_chat.avatar_path)

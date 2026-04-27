from routers.custom_router import APIRouter
from fastapi import Depends
from redis import Redis
from sqlmodel import Session
from starlette.exceptions import HTTPException
from starlette.requests import Request
from dependencies import get_db_session, get_redis_client
from utils import decode_jwt
from models import Chat, ChatMessage
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_pagination
from dependencies import logger

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{chat_id}", response_model=Page[ChatMessage])
async def get_messages_by_chat_id(
    chat_id: str,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    db_client: Session = Depends(get_db_session),
):
    """
    Retrieve paginated chat messages for a specific chat ID.

    This endpoint fetches messages associated with the given `chat_id` and returns them in a paginated format.
    It validates the user's session and ensures that the user has access to the requested chat.

    Args:
        chat_id (str): The unique identifier of the chat whose messages are to be retrieved.
        request (Request): The HTTP request object, used to extract cookies.
        redis_client (Redis): Redis client dependency for session validation.
        db_client (Session): Database session dependency for querying chat messages.

    Returns:
        Page[ChatMessage]: A paginated list of chat messages for the specified chat ID.

    Raises:
        HTTPException: If the session ID is missing, invalid, or the user does not own the chat.

    Notes:
        - The endpoint checks for a `session_id` cookie in the request.
        - The session ID is validated against Redis to retrieve the user's JWT token.
        - The user's ownership of the chat is verified before returning the messages.

    Example:
        GET /messages/{chat_id}

        Response:
        {
            "items": [
                {
                    "id": "message1",
                    "chat_id": "chat123",
                    "content": "Hello, world!",
                    "created_at": "2023-01-01T12:00:00Z"
                },
                ...
            ],
            "total": 10,
            "page": 1,
            "size": 5
        }
    """
    query = db_client.query(ChatMessage)
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error(f"No session_id cookie found for {chat_id}")
        raise HTTPException(status_code=404, detail="Not found")
    token = redis_client.get(f"session:{session_id}")
    claims = decode_jwt(token)
    user_id = claims["oid"]
    query = query.filter(ChatMessage.chat_id == chat_id).order_by(
        ChatMessage.created_at.desc()
    )
    page = sqlalchemy_pagination(query)
    chat: Chat | None = page.items[0].chat if len(page.items) > 0 else None

    if chat and not chat.user_id == user_id:
        logger.error(f"Chat {chat.chat_id} does not belong to {user_id}")
        raise HTTPException(status_code=404, detail="Chat does not belong to you")

    return page

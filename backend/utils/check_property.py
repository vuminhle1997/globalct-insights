from dependencies import logger
from fastapi import HTTPException
from models.chat import Chat
from redis import Redis
from starlette.requests import Request

from backend.utils.jwt import decode_jwt


def check_property_belongs_to_user(request_from_route: Request, redis_client: Redis, chat: "Chat"):
    """
    Verifies if a chat belongs to the authenticated user.

    This function checks if the chat instance belongs to the user making the request by comparing
    the user ID from the session token with the chat's user ID.

    Args:
        request_from_route (Request): The FastAPI request object containing session cookie
        redis_client (Redis): Redis client instance for session management
        chat (Chat): Chat instance to verify ownership

    Returns:
        tuple: A tuple containing:
            - bool: True if chat belongs to user, False otherwise
            - str | None: User ID if validation successful, None otherwise

    Raises:
        HTTPException: If session ID cookie is not found (404 error)
    """
    session_id = request_from_route.cookies.get("session_id")
    if not session_id:
        logger.error("Session id cookie not found")
        raise HTTPException(status_code=404, detail="Session ID not found")
    token = redis_client.get(f"session:{session_id}")
    claims = decode_jwt(token)
    user_id = claims["oid"]
    if chat.user_id != user_id:
        return False, None
    else:
        return True, user_id

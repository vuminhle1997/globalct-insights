import jwt
from fastapi import HTTPException
from redis import Redis
from starlette.requests import Request

from backend.dependencies import logger
from backend.models.chat import Chat


def decode_jwt(token: str) -> dict:
    """Decode an Azure AD JWT token without verifying the signature.

    The token was already validated by Microsoft; we only need to extract claims.

    Args:
        token: Raw JWT string retrieved from Redis.

    Returns:
        Decoded token payload as a dictionary.

    Raises:
        HTTPException 401: If the token is expired or structurally invalid.
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as exc:
        logger.error(f"Invalid token: {exc}")
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_session_and_get_user_id(request: Request, redis_client: Redis) -> tuple[str, str]:
    """Verify session validity and extract user ID from the stored JWT token.

    Steps:
        1. Extract the ``session_id`` cookie from the request.
        2. Retrieve the JWT token from Redis.
        3. Decode the JWT to extract ``oid`` (the Azure object ID used as user_id).

    Args:
        request: The HTTP request object containing the session cookie.
        redis_client: Redis client for session lookup.

    Returns:
        Tuple of (user_id, session_id).

    Raises:
        HTTPException 404: If the session cookie or Redis entry is missing.
        HTTPException 401: If the JWT is invalid or expired.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("Session id cookie not found")
        raise HTTPException(status_code=404, detail="Session Not found")

    token = redis_client.get(f"session:{session_id}")
    if not token:
        logger.error(f"Session {session_id} not found in Redis")
        raise HTTPException(status_code=404, detail="Session Not found")

    claims = decode_jwt(token)
    user_id = claims["oid"]
    return user_id, session_id


def verify_session_exists(request: Request, redis_client: Redis) -> str:
    """Verify that a session exists without decoding the JWT.

    Args:
        request: The HTTP request object containing the session cookie.
        redis_client: Redis client for session lookup.

    Returns:
        The session_id string.

    Raises:
        HTTPException 404: If the session cookie or Redis entry is missing.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("Session id cookie not found")
        raise HTTPException(status_code=404, detail="Session Not found")

    token = redis_client.get(f"session:{session_id}")
    if not token:
        logger.error(f"Session {session_id} not found in Redis")
        raise HTTPException(status_code=404, detail="Session Not found")

    return session_id


def check_property_belongs_to_user(
    request: Request, redis_client: Redis, chat: "Chat"
) -> tuple[bool, str | None]:
    """Verify that a chat belongs to the authenticated user.

    Args:
        request: The FastAPI request object containing the session cookie.
        redis_client: Redis client for session management.
        chat: The Chat ORM instance to check ownership of.

    Returns:
        Tuple of (belongs_to_user: bool, user_id: str | None).

    Raises:
        HTTPException 404: If the session is missing.
    """
    user_id, _ = verify_session_and_get_user_id(request, redis_client)
    if chat.user_id != user_id:
        return False, None
    return True, user_id

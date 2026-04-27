from fastapi import HTTPException
from redis import Redis
from starlette.requests import Request

from backend.dependencies import logger
from backend.utils.jwt import decode_jwt


def verify_session_and_get_user_id(
    request: Request, redis_client: Redis
) -> tuple[str, str]:
    """
    Verify session validity and extract user ID from JWT token.

    This function validates that a session exists and is valid by:
    1. Extracting the session_id cookie from the request
    2. Retrieving the JWT token from Redis
    3. Decoding the JWT token to extract user information

    Args:
        request (Request): The HTTP request object containing session cookie
        redis_client (Redis): Redis client instance for session lookup

    Returns:
        tuple: A tuple containing (user_id, session_id)

    Raises:
        HTTPException:
            - 404 if session_id cookie is not found
            - 404 if session is not found in Redis
            - 401 if JWT token is invalid or expired
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
    """
    Verify that a session exists without decoding JWT.

    This function performs minimal validation to check if a session is valid.

    Args:
        request (Request): The HTTP request object containing session cookie
        redis_client (Redis): Redis client instance for session lookup

    Returns:
        str: The session_id if valid

    Raises:
        HTTPException:
            - 404 if session_id cookie is not found
            - 404 if session is not found in Redis
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

import uuid

import requests
from fastapi import APIRouter, Depends
from msal import ConfidentialClientApplication
from redis import Redis
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from backend.core.config import (
    ALLOWED_GROUPS_IDS,
    AUTHORITY,
    CLIENT_ID,
    CLIENT_SECRET,
    FRONTEND_URL,
    REDIRECT_URI,
    SCOPES,
)
from backend.dependencies import get_redis_client, logger
from backend.services.session_service import decode_jwt

router = APIRouter(tags=["auth"])

_azure_app = ConfidentialClientApplication(CLIENT_ID, CLIENT_SECRET, AUTHORITY)


def _user_is_part_of_group(user_groups: list[str], allowed_groups: list[str]) -> bool:
    return bool(set(user_groups) & set(allowed_groups))


@router.get("/signin")
async def azure_signin(request: Request):
    """
    Initiates the Azure sign-in process by redirecting the user to the Azure authorization URL.

    This endpoint generates an authorization URL for the user to sign in with their Azure account.
    Once the user signs in, they will be redirected to the specified redirect URI.

    Example:
        GET /signin

    Returns:
        RedirectResponse: Redirects the user to the Azure authorization URL.
    """
    auth_url = _azure_app.get_authorization_request_url(SCOPES, redirect_uri=REDIRECT_URI)
    logger.info("Signed in user IP: ", request.client.host)
    return RedirectResponse(url=auth_url)


@router.get("/logout")
def azure_logout(redis_client: Redis = Depends(get_redis_client), request: Request = Request):
    """
    Logs out the user by deleting their session from Redis.

    This endpoint invalidates the user's session by removing the session ID from Redis.
    The user will be redirected to the specified redirect URI after logout.

    Example:
        GET /logout

    Returns:
        RedirectResponse: Redirects the user to the specified redirect URI.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    redis_client.delete(f"session:{session_id}")
    return RedirectResponse(url=FRONTEND_URL)


@router.get("/redirect")
def auth_callback(request: Request, redis_client: Redis = Depends(get_redis_client)):
    """
    Handles the Azure authentication callback and retrieves the access token.

    This endpoint is called after the user signs in with Azure. It processes the authorization
    code and retrieves an access token. The token is stored in Redis, and a session cookie is set.

    Example:
        GET /redirect?code=<authorization_code>

    Args:
        request (Request): The incoming HTTP request.
        redis_client (Redis): Redis client dependency.

    Returns:
        RedirectResponse: Redirects the user to the frontend if successful.
        JSONResponse: Returns an error message if the token retrieval fails.
    """
    code = request.query_params.get("code")
    if not code:
        logger.error(f"No code for Azure found for user: {request.client.host}")
        return JSONResponse({"error": "Authorization code not found"}, status_code=400)

    token_response = _azure_app.acquire_token_by_authorization_code(code, SCOPES, redirect_uri=REDIRECT_URI)

    if "access_token" in token_response:
        session_id = str(uuid.uuid4())
        # Store access token in Redis (expires in 1 hour)
        redis_client.setex(f"session:{session_id}", 3600, token_response["access_token"])
        # Set session cookie
        resp = RedirectResponse(url=f"{FRONTEND_URL}")
        resp.set_cookie("session_id", session_id, httponly=True, secure=False)
        logger.info(f"Successfully logged in: {session_id} for user: {request.client.host}")
        return resp
    else:
        return JSONResponse({"error": "Failed to retrieve access token"}, status_code=400)


@router.get("/me")
async def get_user_claims(request: Request, redis_client: Redis = Depends(get_redis_client)):
    """
    Retrieves the user's claims and group memberships from Microsoft Graph API.

    This endpoint extracts the user's claims and group memberships using the access token
    stored in Redis. It validates whether the user belongs to the allowed groups.

    Example:
        GET /me

    Args:
        request (Request): The incoming HTTP request.
        redis_client (Redis): Redis client dependency.

    Returns:
        dict: A dictionary containing user information and group memberships.

    Raises:
        HTTPException: If the session ID or token is not found, or if the user does not belong
        to the allowed groups.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error(f"No session id for Azure found for user: {request.client.host}")
        return JSONResponse({"error": "Failed to retrieve access token"}, status_code=400)
    token = redis_client.get(f"session:{session_id}")

    claims = decode_jwt(token)
    if claims.get("isDev") is True:
        user = {
            **claims,
        }
        response = {
            "user": user,
            "groups": ALLOWED_GROUPS_IDS,
        }
        return response

    headers = {
        "Authorization": f"Bearer {token}",
    }
    user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()
    group_info = requests.get("https://graph.microsoft.com/v1.0/me/memberOf", headers=headers).json()

    groups: list[str] = list(map(lambda g: g["id"], group_info["value"]))

    if not _user_is_part_of_group(groups, ALLOWED_GROUPS_IDS):
        logger.error(f"User {request.client.host} does not belong to any group: {groups}")
        raise HTTPException(status_code=401, detail="User is not part of the group")

    return {
        "user": user_info,
        "groups": group_info,
    }


@router.get("/profile-picture")
async def get_profile_picture(request: Request, redis_client: Redis = Depends(get_redis_client)):
    """
    Fetches the user's profile picture from Microsoft Graph API.

    This endpoint retrieves the user's profile picture using the access token stored in Redis.
    The profile picture is returned as a JPEG image.

    Example:
        GET /profile-picture

    Args:
        request (Request): The incoming HTTP request.
        redis_client (Redis): Redis client dependency.

    Returns:
        Response: The profile picture as a JPEG image.

    Raises:
        HTTPException: If the session ID or token is not found, or if the profile picture
        cannot be retrieved due to an error or invalid token.
    """
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/photo/$value"
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error(f"No session id for Azure found for user: {request.client.host}")
        raise HTTPException(status_code=400, detail="Session ID not found")

    token = redis_client.get(f"session:{session_id}")
    if not token:
        logger.error(f"No session id for Azure found for user: {request.client.host}")
        raise HTTPException(status_code=401, detail="Token not found in Redis")

    response = requests.get(GRAPH_API_URL, headers={"Authorization": f"Bearer {token}"})

    if response.status_code == 200:
        return Response(content=response.content, media_type="image/jpeg")
    elif response.status_code == 401:
        logger.error(f"Failed to get session id for user: {request.client.host}")
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or expired token")
    elif response.status_code == 404:
        logger.error(f"Failed to get session id for user: {request.client.host}")
        raise HTTPException(status_code=404, detail="Profile picture not found")
    else:
        logger.error(f"Failed to get session id for user: {request.client.host}")
        raise HTTPException(status_code=500, detail="Error fetching profile picture")

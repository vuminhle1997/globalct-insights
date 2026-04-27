import datetime
import os

import jwt
from dependencies import logger
from fastapi import HTTPException

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"


def decode_jwt(token: str):
    """Decodes and verifies the JWT token.

    This function attempts to decode a JWT token without signature verification.
    If the token is expired or invalid, appropriate HTTP exceptions are raised.

    Args:
        token (str): The JWT token string to decode

    Returns:
        dict: The decoded token payload as a dictionary

    Raises:
        HTTPException: If token is expired (401) or invalid (401)
    """
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})  # No signature verification for now
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.error(f"Token expired {token}")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        logger.error(f"Invalid token {token}")
        raise HTTPException(status_code=401, detail="Invalid token")


def create_jwt(oid: str, name: str, last_name: str, email: str) -> str:
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    payload = {
        "id": oid,
        "oid": oid,
        "name": name,
        "surname": last_name,
        "displayName": f"{name} {last_name}",
        "givenName": f"{name} {last_name}",
        "officeLocation": "Berlin",
        "jobTitle": "Tester",
        "email": email,
        "userPrincipalName": email,
        "isDev": True,
        "exp": expiration,
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

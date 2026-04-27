import uuid

from redis import Redis
from sqlmodel import Session
from routers.custom_router import APIRouter
from fastapi import Depends, Response

from dependencies import get_db_session, get_redis_client, logger
from models.user import UserLogin
from utils import create_jwt
from models import UserCreate, User
from typing import List

import bcrypt
import re

email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def create_user(
    user: UserCreate,
    db_client: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Create a new user and handle session management.

    This endpoint allows the creation of a new user by validating the provided
    email and password, hashing the password, and storing the user in the database.
    It also generates a JWT token for the user session and stores it in Redis.

    Args:
        user (UserCreate): The user data containing name, last name, email, password,
            and confirm_password.
        db_client (Session): The database session dependency for interacting with the database.
        redis_client (Redis): The Redis client dependency for session management.

    Returns:
        Response: A response object indicating the result of the operation:
            - 200: Login successful, with a session cookie set.
            - 401: Invalid email or mismatched passwords.
            - 500: Internal server error if an exception occurs.

    Raises:
        Exception: Logs and returns an error response if any exception occurs during
            user creation or session management.
    """
    if not bool(re.match(email_pattern, user.email)):
        return Response("Email is not valid.", status_code=401)
    if user.password != user.confirm_password:
        return Response("Password is not matching.", status_code=401)
    hashed_password = bcrypt.hashpw(user.password.encode("utf8"), bcrypt.gensalt(12))
    db_user = User(
        id=str(uuid.uuid4()),
        name=user.name,
        last_name=user.last_name,
        email=user.email,
        hashed_password=hashed_password.decode("utf8"),
    )

    try:
        db_client.add(db_user)
        db_client.commit()

        session_id = str(uuid.uuid4())
        jwt_token = create_jwt(
            oid=db_user.id, name=user.name, last_name=user.last_name, email=user.email
        )
        redis_client.setex(f"session:{session_id}", 3600, jwt_token)
        response = Response("Login successful.", status_code=200)
        response.set_cookie(
            "session_id", session_id, httponly=False, secure=False
        )  # set on True when Production
        return response
    except Exception as e:
        logger.error(e)
        return Response(e, status_code=500)


@router.post("/login/")
async def login_user(
    user: UserLogin,
    db_client: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Handles user login requests.

    This endpoint validates the user's email and password, checks the credentials
    against the database, and generates a session ID and JWT token upon successful
    authentication. The session ID is stored in Redis with a 1-hour expiration time,
    and a cookie containing the session ID is set in the response.

    Args:
        user (UserLogin): The user login data containing email and password.
        db_client (Session): The database session dependency.
        redis_client (Redis): The Redis client dependency.

    Returns:
        Response:
            - 200: Login successful. Sets a session cookie and returns a success message.
            - 401: Invalid email, missing password, or incorrect password.
            - 404: User not found in the database.
            - 500: Internal server error.

    Raises:
        Exception: Logs and returns an error response in case of unexpected issues.
    """
    if not bool(re.match(email_pattern, user.email)):
        return Response("Email is not valid.", status_code=401)
    if not user.password:
        return Response("Password is missing.", status_code=401)
    try:
        db_user: List[User] | None = (
            db_client.query(User).filter(User.email.like(f"%{user.email}%")).all()
        )

        if db_user and len(db_user) > 0:
            db_user: User = db_user[0]
            is_matching = bcrypt.checkpw(
                user.password.encode(), db_user.hashed_password.encode()
            )
            if is_matching:
                session_id = str(uuid.uuid4())
                jwt_token = create_jwt(
                    oid=db_user.id,
                    name=db_user.name,
                    last_name=db_user.last_name,
                    email=db_user.email,
                )
                redis_client.setex(f"session:{session_id}", 3600, jwt_token)
                response = Response("Login successful.", status_code=200)
                response.set_cookie(
                    "session_id", session_id, httponly=False, secure=False
                )  # set on True when Production
                return response
            else:
                return Response("Password wrong.", status_code=401)
        else:
            return Response("User not found.", status_code=404)
    except Exception as e:
        logger.error(e)
        return Response(e, status_code=500)

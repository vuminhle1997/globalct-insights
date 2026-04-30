import uuid

from fastapi import Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_pagination
from redis import Redis
from sqlalchemy.orm import selectinload
from sqlmodel import Session
from starlette.exceptions import HTTPException
from starlette.requests import Request

from backend.core.serializers import serialize_chat, serialize_favourite
from backend.dependencies import get_db_session, get_redis_client, logger
from backend.models.chat import Chat
from backend.models.favourite import Favourite, FavouritePublic
from backend.routers.custom_router import APIRouter
from backend.services.session_service import check_property_belongs_to_user, verify_session_and_get_user_id

router = APIRouter(
    prefix="/favourites",
    tags=["favourites"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=Page[FavouritePublic])
async def get_favourites_of_user(
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    db_client: Session = Depends(get_db_session),
):
    """
    Retrieve paginated list of favourites for the authenticated user.

    This endpoint fetches all favourite chats associated with the authenticated
    user and returns them in a paginated format.

    Args:
        request (Request): The HTTP request object, used to extract cookies.
        redis_client (Redis): Redis client dependency for session validation.
        db_client (Session): Database session dependency for querying favourites.

    Returns:
        Page[Favourite]: A paginated list of favourites for the authenticated user.

    Raises:
        HTTPException: If the session ID is missing or invalid.

    Notes:
        - The endpoint checks for a `session_id` cookie in the request.
        - The session ID is validated against Redis to retrieve the user's JWT token.
        - Only favourites belonging to the authenticated user are returned.

    Example:
        GET /favourites/

        Response:
        {
            "items": [
                {
                    "id": "favourite1",
                    "user_id": "user123",
                    "chat_id": "chat123",
                    "chat": {
                        "id": "chat123",
                        "name": "Chat Name",
                        "created_at": "2023-01-01T12:00:00Z"
                    }
                },
                ...
            ],
            "total": 5,
            "page": 1,
            "size": 5
        }
    """
    query = db_client.query(Favourite).join(Chat).options(selectinload(Favourite.chat))
    user_id, _ = verify_session_and_get_user_id(request, redis_client)
    query = query.filter(Favourite.user_id == user_id)
    page = sqlalchemy_pagination(query)
    items: list[Favourite] = page.items

    items = [
        {
            **serialize_favourite(item),
            "chat": serialize_chat(item.chat),
        }
        for item in items
    ]
    page.items = items
    return page


@router.get("/{chat_id}")
async def get_favourite_of_chat(
    chat_id: str,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    db_client: Session = Depends(get_db_session),
):
    """
    Retrieve the favourite status of a specific chat.

    This endpoint fetches the favourite status of a chat identified by `chat_id` for the authenticated user.

    Args:
        chat_id (str): The unique identifier of the chat.
        request (Request): The HTTP request object, used to extract cookies.
        redis_client (Redis): Redis client dependency for session validation.
        db_client (Session): Database session dependency for querying the chat and its favourite status.

    Returns:
        dict: A dictionary containing the chat details and its favourite status.

    Raises:
        HTTPException: If the chat is not found, does not belong to the user, or does not have a favourite status.

    Notes:
        - The endpoint checks if the chat exists in the database.
        - It validates that the chat belongs to the authenticated user.
        - If the chat is not marked as a favourite, an error is raised.

    Example:
        GET /favourites/{chat_id}

        Response:
        {
            "id": "chat123",
            "name": "Chat Name",
            "created_at": "2023-01-01T12:00:00Z",
            "favourite": {
                "id": "favourite1",
                "user_id": "user123",
                "chat_id": "chat123"
            }
        }
    """
    db_chat: Chat | None = (
        db_client.query(Chat).options(selectinload(Chat.favourite)).get(chat_id)
    )
    if not db_chat:
        logger.error(f"Chat {chat_id} not found in database")
        raise HTTPException(status_code=404, detail="Chat not found")
    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    if not db_chat.favourite:
        logger.error(f"Favourite for chat {chat_id} not found in database")
        raise HTTPException(status_code=404, detail="Favourite not found")
    return {
        **serialize_chat(db_chat),
        "favourite": serialize_favourite(db_chat.favourite),
    }


@router.post("/{chat_id}")
async def favour_chat_by_id(
    chat_id: str,
    request: Request,
    redis_client: Redis = Depends(get_redis_client),
    db_client: Session = Depends(get_db_session),
):
    """
    Mark a chat as a favourite for the authenticated user.

    This endpoint allows the authenticated user to mark a chat identified by `chat_id` as a favourite.

    Args:
        chat_id (str): The unique identifier of the chat to be marked as a favourite.
        request (Request): The HTTP request object, used to extract cookies.
        redis_client (Redis): Redis client dependency for session validation.
        db_client (Session): Database session dependency for updating the favourite status.

    Returns:
        dict: A dictionary containing the details of the newly created favourite.

    Raises:
        HTTPException: If the chat does not belong to the user or if an error occurs during the operation.

    Notes:
        - The endpoint validates that the chat belongs to the authenticated user.
        - A new favourite record is created and associated with the chat.

    Example:
        POST /favourites/{chat_id}

        Response:
        {
            "id": "favourite1",
            "user_id": "user123",
            "chat_id": "chat123"
        }
    """
    db_chat: type[Chat] = (
        db_client.query(Chat).options(selectinload(Chat.favourite)).get(chat_id)
    )
    belongs_to_user, user_id = check_property_belongs_to_user(
        request, redis_client, db_chat
    )

    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    db_favourites = Favourite(
        id=str(uuid.uuid4()),
        user_id=user_id,
        chat_id=db_chat.id,
    )

    try:
        db_chat.favourite = db_favourites
        db_client.add(db_favourites)
        db_client.commit()
        db_client.refresh(db_favourites)
        # Reload the favourite with chat relationship
        db_favourites = (
            db_client.query(Favourite)
            .options(selectinload(Favourite.chat))
            .get(db_favourites.id)
        )
        return {
            **serialize_favourite(db_favourites),
            "chat": serialize_chat(db_favourites.chat),
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chat_id}")
async def delete_favourite_of_chat_by(
    chat_id: str,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    db_client: Session = Depends(get_db_session),
):
    """
    Remove the favourite status of a specific chat.

    This endpoint allows the authenticated user to remove the favourite status of a chat identified by `chat_id`.

    Args:
        chat_id (str): The unique identifier of the chat whose favourite status is to be removed.
        request (Request): The HTTP request object, used to extract cookies.
        redis_client (Redis): Redis client dependency for session validation.
        db_client (Session): Database session dependency for removing the favourite status.

    Returns:
        dict: A dictionary containing the details of the removed favourite and the associated chat.

    Raises:
        HTTPException: If the chat does not belong to the user, does not have a favourite status, or if an error occurs.

    Notes:
        - The endpoint validates that the chat belongs to the authenticated user.
        - The favourite record associated with the chat is deleted.

    Example:
        DELETE /favourites/{chat_id}

        Response:
        {
            "id": "favourite1",
            "user_id": "user123",
            "chat_id": "chat123",
            "chat": {
                "id": "chat123",
                "name": "Chat Name",
                "created_at": "2023-01-01T12:00:00Z"
            }
        }
    """
    db_chat: type[Chat] = (
        db_client.query(Chat).options(selectinload(Chat.favourite)).get(chat_id)
    )
    belongs_to_user, user_id = check_property_belongs_to_user(
        request, redis_client, db_chat
    )
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    if not db_chat.favourite:
        logger.error(f"Favourite for chat {chat_id} not found in database")
        raise HTTPException(status_code=404, detail="Favourite not found")

    db_favourites: Favourite = db_chat.favourite

    try:
        db_client.delete(db_favourites)
        db_client.commit()
        return {
            **serialize_favourite(db_favourites),
            **serialize_chat(db_chat),
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

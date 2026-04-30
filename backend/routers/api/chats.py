import json
import uuid
from datetime import datetime
from pathlib import Path

from chromadb import Collection
from fastapi import Depends, File, Form, HTTPException, Response, UploadFile
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_pagination
from redis import Redis
from starlette.requests import Request

from backend.core.serializers import serialize_chat, serialize_chat_message, serialize_favourite
from backend.dependencies import (
    SessionDep,
    get_chroma_collection,
    get_redis_client,
    logger,
)
from backend.models.chat import Chat, ChatPublic
from backend.models.chat_file import ChatFile
from backend.models.chat_message import ChatMessage
from backend.routers.custom_router import APIRouter
from backend.services.migration.db_migration_manager import delete_database_from_postgres
from backend.services.rag.indexer.files_indexer import deletes_file_index_from_collection
from backend.services.session.session_service import check_property_belongs_to_user, verify_session_and_get_user_id

BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
    responses={404: {"description": "Not found"}},
)


# ---------------------------------------------------------------------------
# CRUD endpoints only — AI inference endpoints live in chat_inference.py
# ---------------------------------------------------------------------------


@router.get("/", response_model=Page[ChatPublic])
async def get_chats(
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Retrieve all chats for the authenticated user.

    This endpoint fetches all chats associated with the authenticated user,
    ordered by the last interaction timestamp in descending order.

    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - A paginated list of chats.

    **Raises**:
    - 404: If the session ID is not found in cookies or the user is not authenticated.
    """
    query = db_client.query(Chat)
    user_id, _ = verify_session_and_get_user_id(request, redis_client)
    query = query.filter(Chat.user_id == user_id).order_by(Chat.last_interacted_at.desc())
    page = sqlalchemy_pagination(query)
    return page


@router.get("/search")
async def get_chats_by_title(
    title: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Search chats by title for the authenticated user.

    This endpoint allows the user to search for chats by their title.

    - **title**: The title or partial title of the chat to search for.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - A list of chats matching the title.

    **Raises**:
    - 404: If the session ID is not found in cookies or the user is not authenticated.
    """
    user_id, _ = verify_session_and_get_user_id(request, redis_client)
    chats = db_client.query(Chat).filter(Chat.title.like(f"%{title}%")).filter(Chat.user_id == user_id).all()

    return chats


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Retrieve a specific chat by its ID.

    This endpoint fetches a chat and its associated messages for the authenticated user.

    - **chat_id**: The unique identifier of the chat.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - The chat details, including files, messages, and favorite status.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    """
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
    messages = (
        db_client.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .all()
    )[:10]

    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get favorite status
    favorite = db_chat.favourite if db_chat.favourite else None

    return {
        **serialize_chat(db_chat, include_files=True),
        "messages": [serialize_chat_message(message) for message in messages],
        "favourite": serialize_favourite(favorite),
    }


@router.post("/")
async def create_chat(
    chat: str = Form(...),
    file: UploadFile | None = None,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Create a new chat.

    This endpoint allows the user to create a new chat. Optionally, an avatar image
    can be uploaded for the chat.

    - **chat**: The chat data in JSON format.
    - **file**: Optional avatar image file.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - The created chat details.

    **Raises**:
    - 404: If the session ID is not found in cookies.
    - 400: If the avatar image format is invalid.
    """
    user_id, _ = verify_session_and_get_user_id(request, redis_client)

    chat_id = str(uuid.uuid4())
    avatar_path = None

    if file and file.filename:
        # Get file extension
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif"]:
            logger.error("Invalid image format for chat avatar")
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Create avatars directory if it doesn't exist
        avatar_dir = BASE_UPLOAD_DIR / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        avatar_path = avatar_dir / f"{chat_id}.{ext}"
        with open(avatar_path, "wb+") as buffer:
            buffer.write(file.file.read())

    chat_data = json.loads(chat)
    db_chat = Chat(**chat_data, user_id=user_id, id=chat_id, avatar_path=str(avatar_path))

    try:
        db_client.add(db_chat)
        db_client.commit()
        db_client.refresh(db_chat)
    except Exception as e:
        logger.error(e)
        db_client.rollback()
        return Response(status_code=500, content="Chat create error.")

    return {
        **serialize_chat(db_chat, include_files=True),
    }


@router.put("/{chat_id}")
async def update_chat(
    chat_id: str,
    chat: str = Form(...),
    file: UploadFile = File(None),
    request: Request = Request,
    db_client: SessionDep = SessionDep,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Update an existing chat.

    This endpoint allows the user to update the details of an existing chat. Optionally,
    a new avatar image can be uploaded.

    - **chat_id**: The unique identifier of the chat.
    - **chat**: The updated chat data in JSON format.
    - **file**: Optional new avatar image file.
    - **request**: HTTP request object to extract cookies.
    - **db_client**: Database session dependency.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - The updated chat details.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    - 400: If the avatar image format is invalid.
    """
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    avatar_path = None

    if file and file.filename:
        # Get file extension
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
            logger.error("Invalid image format for chat avatar")
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Create avatars directory if it doesn't exist
        avatar_dir = BASE_UPLOAD_DIR / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # Save new file
        avatar_path = avatar_dir / f"{chat_id}.{ext}"
        with open(avatar_path, "wb+") as buffer:
            buffer.write(file.file.read())

    # Update mutable chat fields explicitly (SQLAlchemy model, no sqlmodel_update helper).
    chat_data = json.loads(chat)
    updatable_fields = {
        "title",
        "description",
        "context",
        "temperature",
        "model",
        "model_provider",
    }
    for field_name in updatable_fields:
        if field_name in chat_data:
            setattr(db_chat, field_name, chat_data[field_name])
    if avatar_path:
        db_chat.avatar_path = str(avatar_path)

    db_chat.last_interacted_at = datetime.now()
    db_client.add(db_chat)
    db_client.commit()
    db_client.refresh(db_chat)

    return {
        **serialize_chat(db_chat, include_files=True),
    }


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    chroma_collection: Collection = Depends(get_chroma_collection),
):
    """
    Delete a chat.

    This endpoint allows the user to delete a chat and all its associated files,
    messages, and avatar.

    - **chat_id**: The unique identifier of the chat.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.
    - **chroma_collection**: Dependency for vector store operations.

    **Returns**:
    - The deleted chat details.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    """
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    files = db_chat.files
    for _file in files:
        deletes_file_index_from_collection(file_id=_file.id, chroma_collection=chroma_collection)

    # Get chat folder path and delete all files inside
    chat_folder = BASE_UPLOAD_DIR / str(chat_id)
    if chat_folder.exists():
        for file in chat_folder.iterdir():
            file.unlink()  # Delete each file
        chat_folder.rmdir()  # Remove the folder itself

    # Delete avatar file if it exists
    if db_chat.avatar_path and Path(db_chat.avatar_path).exists():
        Path(db_chat.avatar_path).unlink()

    db_client.delete(db_chat)
    db_client.commit()
    return {
        **serialize_chat(db_chat),
    }


@router.delete("/{chat_id}/delete/{file_id}")
async def delete_file_of_chat(
    chat_id: str,
    file_id: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    chroma_collection: Collection = Depends(get_chroma_collection),
):
    """
    Delete a file from a chat.

    This endpoint allows the user to delete a specific file from a chat. If the file
    is an SQL dump, the associated database will also be deleted.

    - **chat_id**: The unique identifier of the chat.
    - **file_id**: The unique identifier of the file.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.
    - **chroma_collection**: Dependency for vector store operations.

    **Returns**:
    - The updated chat details after file deletion.

    **Raises**:
    - 404: If the chat or file is not found, or the file does not belong to the chat.
    """
    # If chat is not existing, raise Error
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    # If file is not existing or does not belong to Chat, raise Error
    db_file = db_client.get(ChatFile, file_id)
    if not db_file or db_file.chat_id != chat_id:
        logger.error(f"{db_file.file_name} not found or does not belong to Chat")
        raise HTTPException(status_code=404, detail="File not found or does not belong to this chat")

    # Construct file path and delete from disk
    file_path = BASE_UPLOAD_DIR / str(chat_id) / db_file.file_name
    if file_path.exists():
        file_path.unlink()  # Delete file from storage

    if db_file.mime_type.find("sql") != -1:
        # delete sql database
        delete_database_from_postgres(db_file.database_name)
    else:
        # deletes index from DB
        deletes_file_index_from_collection(chroma_collection=chroma_collection, file_id=db_file.id)
    # Remove file record from the database
    db_client.delete(db_file)
    db_chat.last_interacted_at = datetime.now()
    db_client.commit()
    db_client.refresh(db_chat)

    return {
        **serialize_chat(db_chat, include_files=True),
    }

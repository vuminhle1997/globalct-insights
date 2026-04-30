from backend.models.chat import Chat
from backend.models.chat_file import ChatFile
from backend.models.chat_message import ChatMessage
from backend.models.favourite import Favourite


def serialize_chat_file(chat_file: ChatFile) -> dict:
    return {
        "id": chat_file.id,
        "file_name": chat_file.file_name,
        "path_name": chat_file.path_name,
        "mime_type": chat_file.mime_type,
        "indexed": chat_file.indexed,
        "chat_id": chat_file.chat_id,
        "database_name": chat_file.database_name,
        "database_type": chat_file.database_type,
        "tables": chat_file.tables,
        "created_at": chat_file.created_at,
        "updated_at": chat_file.updated_at,
    }


def serialize_chat_message(chat_message: ChatMessage) -> dict:
    return {
        "id": chat_message.id,
        "role": chat_message.role,
        "additional_kwargs": chat_message.additional_kwargs,
        "block_type": chat_message.block_type,
        "text": chat_message.text,
        "created_at": chat_message.created_at,
        "chat_id": chat_message.chat_id,
    }


def serialize_favourite(favourite: Favourite | None) -> dict | None:
    if favourite is None:
        return None

    return {
        "id": favourite.id,
        "created_at": favourite.created_at,
        "chat_id": favourite.chat_id,
        "user_id": favourite.user_id,
    }


def serialize_chat(chat: Chat, *, include_files: bool = False) -> dict:
    serialized_chat = {
        "id": chat.id,
        "title": chat.title,
        "description": chat.description,
        "context": chat.context,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "last_interacted_at": chat.last_interacted_at,
        "user_id": chat.user_id,
        "avatar_path": chat.avatar_path,
        "temperature": chat.temperature,
        "model": chat.model,
    }
    if include_files:
        serialized_chat["files"] = [serialize_chat_file(chat_file) for chat_file in chat.files]
    return serialized_chat

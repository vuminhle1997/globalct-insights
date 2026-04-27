import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

from . import Base

if TYPE_CHECKING:
    from models.chat import Chat


class BaseChatFile(SQLModel):
    file_name: str = Field(index=True, nullable=False)
    path_name: str = Field(index=True, nullable=False)
    mime_type: str = Field(index=True, nullable=False)
    indexed: bool = Field(nullable=True)
    chat_id: str | None = Field(default=None, foreign_key="chats.id")
    database_name: str | None = Field(default=None, nullable=True, index=True)
    database_type: str | None = Field(default=None, nullable=True, index=True)
    tables: list[str] | None = Field(default=None, sa_column=Column(JSON))


class ChatFile(BaseChatFile, Base, table=True):
    __tablename__ = "chat_files"
    id: str = Field(primary_key=True, nullable=False, default=str(uuid.uuid4()))
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    chat: "Chat" = Relationship(back_populates="files")


class ChatFilePublic(BaseChatFile):
    id: str
    created_at: datetime
    updated_at: datetime
    chat: "Chat"


class ChatFileCreate(BaseChatFile):
    pass


class ChatFileUpdate(BaseChatFile):
    pass

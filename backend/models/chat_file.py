import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import ForeignKey, JSON, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from models.chat import Chat


class ChatFile(Base):
    __tablename__ = "chat_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    path_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    indexed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    chat_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("chats.id"), default=None
    )
    database_name: Mapped[str | None] = mapped_column(String, default=None, nullable=True, index=True)
    database_type: Mapped[str | None] = mapped_column(String, default=None, nullable=True, index=True)
    tables: Mapped[list[str] | None] = mapped_column(JSON, default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="files")


class ChatFilePublic(BaseModel):
    id: str
    file_name: str
    path_name: str
    mime_type: str
    indexed: bool | None
    chat_id: str | None
    database_name: str | None
    database_type: str | None
    tables: list[str] | None
    created_at: datetime
    updated_at: datetime


class ChatFileCreate(BaseModel):
    file_name: str
    path_name: str
    mime_type: str
    indexed: bool | None = None
    chat_id: str | None = None
    database_name: str | None = None
    database_type: str | None = None
    tables: list[str] | None = None


class ChatFileUpdate(BaseModel):
    file_name: str
    path_name: str
    mime_type: str
    indexed: bool | None = None
    chat_id: str | None = None
    database_name: str | None = None
    database_type: str | None = None
    tables: list[str] | None = None

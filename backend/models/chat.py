import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from models.chat_file import ChatFile
    from models.chat_message import ChatMessage
    from models.favourite import Favourite


class FileParams(BaseModel):
    queried: bool
    query_type: str


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, index=True, default=datetime.now)
    last_interacted_at: Mapped[datetime] = mapped_column(nullable=False, index=True, default=datetime.now)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    avatar_path: Mapped[str] = mapped_column(String, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, index=True, default=0.75)
    model: Mapped[str] = mapped_column(String, nullable=False, index=True, default="llama3.1")

    files: Mapped[list["ChatFile"]] = relationship(
        "ChatFile", back_populates="chat", cascade="all, delete"
    )
    favourite: Mapped["Favourite"] = relationship(
        "Favourite", back_populates="chat", cascade="all, delete"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="chat", cascade="all, delete"
    )


class ChatPublic(BaseModel):
    id: str
    title: str
    description: str | None
    context: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    files: list["ChatFile"] = []


class ChatCreate(BaseModel):
    title: str
    temperature: float
    description: str | None
    context: str


class ChatUpdate(BaseModel):
    title: str
    temperature: float
    description: str | None
    context: str


class ChatParams(BaseModel):
    use_websearch: bool
    use_link_scraping: bool
    files: dict[str, FileParams] | None = {}


class ChatQuery(BaseModel):
    text: str
    params: ChatParams

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base
from backend.models.chat_file import ChatFilePublic

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
    model_provider: Mapped[str] = mapped_column(String, nullable=False, index=True, default="GOOGLE_GENAI")

    files: Mapped[list["ChatFile"]] = relationship("ChatFile", back_populates="chat", cascade="all, delete")
    favourite: Mapped["Favourite"] = relationship("Favourite", back_populates="chat", cascade="all, delete")
    messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="chat", cascade="all, delete")


class ChatPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    context: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_interacted_at: datetime
    avatar_path: str
    temperature: float
    model: str
    model_provider: str
    files: list[ChatFilePublic] = Field(default_factory=list)


class ChatCreate(BaseModel):
    title: str
    temperature: float
    description: str | None
    context: str
    model_provider: str = "GOOGLE_GENAI"


class ChatUpdate(BaseModel):
    title: str
    temperature: float
    description: str | None
    context: str
    model_provider: str = "GOOGLE_GENAI"


class ChatParams(BaseModel):
    use_websearch: bool
    use_link_scraping: bool
    files: dict[str, FileParams] | None = {}


class ChatQuery(BaseModel):
    text: str
    params: ChatParams

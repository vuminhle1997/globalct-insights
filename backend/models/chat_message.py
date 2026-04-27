import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from models.chat import Chat


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    additional_kwargs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    block_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), nullable=False, index=True)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")


class ChatMessageCreate(BaseModel):
    role: str
    additional_kwargs: dict
    block_type: str
    text: str

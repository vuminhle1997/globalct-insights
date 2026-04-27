import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from . import Base

if TYPE_CHECKING:
    from models.chat import Chat


class ChatMessageBase(SQLModel):
    role: str = Field(nullable=False)
    additional_kwargs: dict = Field(sa_type=JSONB, nullable=False)
    block_type: str = Field(nullable=False, index=True)
    text: str = Field(nullable=False, index=True)


class ChatMessage(ChatMessageBase, Base, table=True):
    __tablename__ = "chat_messages"
    id: str = Field(primary_key=True, default=str(uuid.uuid4()), index=True)
    role: str = Field(nullable=False)
    additional_kwargs: dict = Field(sa_type=JSONB, nullable=False, default={})
    block_type: str = Field(nullable=False, index=True)
    text: str = Field(nullable=False, index=True)
    created_at: datetime = Field(nullable=False, default=datetime.now())
    chat_id: str = Field(nullable=False, index=True, foreign_key="chats.id")
    chat: "Chat" = Relationship(back_populates="messages")


class ChatMessageCreate(ChatMessageBase):
    role: str
    additional_kwargs: dict
    block_type: str
    text: str

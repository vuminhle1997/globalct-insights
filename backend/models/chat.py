import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from . import Base

if TYPE_CHECKING:
    from models.chat_file import ChatFile
    from models.chat_message import ChatMessage
    from models.favourite import Favourite


class FileParams(BaseModel):
    queried: bool
    query_type: str


class ChatBase(SQLModel):
    title: str = Field(nullable=False, index=True)
    description: str = Field(nullable=True, index=True)
    context: str = Field(nullable=False)


class Chat(ChatBase, Base, table=True):
    __tablename__ = "chats"
    id: str = Field(primary_key=True, default=str(uuid.uuid4()))
    created_at: datetime = Field(nullable=False, index=True, default=datetime.now())
    updated_at: datetime = Field(nullable=False, index=True, default=datetime.now())
    last_interacted_at: datetime = Field(nullable=False, index=True, default=datetime.now())
    user_id: str = Field(nullable=False, index=True)
    avatar_path: str = Field(nullable=False)
    temperature: float = Field(nullable=False, index=True, default=0.75)
    model: str = Field(nullable=False, index=True, default="llama3.1")
    files: list["ChatFile"] = Relationship(back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete"})
    favourite: "Favourite" = Relationship(back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete"})
    messages: list["ChatMessage"] = Relationship(
        back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete"}
    )


class ChatPublic(ChatBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    files: list["ChatFile"]


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

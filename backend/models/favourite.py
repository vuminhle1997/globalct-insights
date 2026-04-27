import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base
from backend.models.chat import ChatPublic

if TYPE_CHECKING:
    from models.chat import Chat


class Favourite(Base):
    __tablename__ = "favourites"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True, default=datetime.now)
    chat_id: Mapped[str | None] = mapped_column(String, ForeignKey("chats.id"), index=True, default=None)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="favourite")


class FavouritePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    chat_id: str | None
    user_id: str
    chat: ChatPublic | None = None

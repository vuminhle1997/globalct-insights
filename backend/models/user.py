import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, index=True, default=datetime.now)


class UserCreate(BaseModel):
    email: str
    name: str
    last_name: str
    password: str
    confirm_password: str


class UserLogin(BaseModel):
    email: str
    password: str

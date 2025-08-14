
"""Relational models required for authentication.

The application previously defined SQLAlchemy ORM models for WireGuard
servers and peers. Those have been removed in favor of the JSON / MongoDB
metadata repository abstraction implemented in `repository.py`. Retaining
only the `User` model keeps the relational schema minimal and avoids the
confusion of an unused second metadata source.

`Base` is imported from `database` so there is a single declarative base
throughout the project.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from fastapi_users.db import SQLAlchemyBaseUserTable

from .database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Optional display name; nullable to avoid registration constraint failures.
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, default="", server_default="")

__all__ = ["User"]

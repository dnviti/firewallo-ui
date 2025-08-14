
from typing import Generator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.orm import Session
from app.wireguard_manager.models import User
from app.wireguard_manager.database import SessionLocal


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_db(session: Session = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)


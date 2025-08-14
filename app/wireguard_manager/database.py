"""Database bootstrap logic.

This module now supports selecting the metadata storage (servers/peers) backend
via the environment variable DATABASE_TYPE. Supported values:
  - "mongodb": use Motor (async MongoDB driver) connecting to MONGO_URI and MONGO_DB_NAME
  - "litedb": use a local JSON document store (simple, file‑based) located at app/db/metadata.json

Irrespective of metadata backend, the SQLAlchemy engine is still provided for
user authentication (fastapi-users) which currently relies on relational tables.
"""

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------ SQLAlchemy (still used for users) ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, '..', 'db', 'wg_config.db')}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------ Metadata backend selection ------------------
DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "litedb").strip().lower()

if DATABASE_TYPE not in ("mongodb", "litedb"):
    raise ValueError("DATABASE_TYPE must be either 'mongodb' or 'litedb'")

# Mongo configuration (only initialized if selected)
MONGO_URI: Optional[str] = None
MONGO_DB_NAME: Optional[str] = None
mongo_client = None
mongo_db = None

if DATABASE_TYPE == "mongodb":
    try:
        from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("motor must be installed to use mongodb backend") from e

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "firewallo")
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]

# LiteDB (JSON file) configuration
LITE_DB_FILE = Path(BASE_DIR).parent / "db" / "metadata.json"
LITE_DB_FILE.parent.mkdir(parents=True, exist_ok=True)

def ensure_litedb_file():
    if not LITE_DB_FILE.exists():
        LITE_DB_FILE.write_text('{"servers": [], "peers": []}', encoding="utf-8")

if DATABASE_TYPE == "litedb":
    ensure_litedb_file()

__all__ = [
    "SessionLocal",
    "Base",
    "engine",
    "DATABASE_TYPE",
    "mongo_db",
    "mongo_client",
    "LITE_DB_FILE",
]
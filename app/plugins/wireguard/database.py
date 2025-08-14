"""Database bootstrap logic.

This module supports selecting the metadata storage (servers/peers/users) backend
via the environment variable DATABASE_TYPE. Supported values:
  - "mongodb": use Motor (async MongoDB driver) connecting to MONGO_URI and MONGO_DB_NAME
  - "litedb": use a local JSON document store (simple, file‑based) located at app/db/metadata.json

All data including user authentication is handled by the selected backend.
"""

import json
import os
from pathlib import Path
from typing import Optional

# Get the base directory for file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    """Ensure the LiteDB file exists with proper structure."""
    if not LITE_DB_FILE.exists():
        # New modular structure with sections for plugins, core, and auth
        default_structure = {
            "plugins": {
                "vpn": {
                    "wireguard": {
                        "servers": [],
                        "peers": []
                    }
                }
            },
            "core": {
                "system": {},
                "config": {},
                "logs": []
            },
            "auth": {
                "users": [],
                "rbac": {
                    "roles": [],
                    "permissions": [],
                    "assignments": []
                }
            }
        }
        LITE_DB_FILE.write_text(json.dumps(default_structure, indent=2), encoding="utf-8")

if DATABASE_TYPE == "litedb":
    ensure_litedb_file()

__all__ = [
    "DATABASE_TYPE",
    "mongo_db",
    "mongo_client",
    "LITE_DB_FILE",
    "ensure_litedb_file",
]
"""ASGI entrypoint (refactored).

Business logic & routes moved to modular packages under app/.
No SQLite dependencies - using LiteDB or MongoDB for all data.
"""
from __future__ import annotations

from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
from app.core.config import create_app
from app.core.startup import create_default_admin
from app.api.routes import servers, peers, gui, auth


app = create_app()


@app.on_event("startup")
def _startup():
    """Application startup tasks."""
    create_default_admin()


# API Router setup
api_router = APIRouter(prefix="/api")
api_router.include_router(servers.router)
api_router.include_router(peers.router)
api_router.include_router(auth.router, prefix="/auth")

# Include routers
app.include_router(api_router)
app.include_router(gui.router)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


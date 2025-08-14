"""ASGI entrypoint (refactored).

Business logic & routes moved to modular packages under app/.
"""
from __future__ import annotations

from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
from app.core.config import create_app
from app.users.users import fastapi_users, auth_backend
from app.users.schemas import UserRead, UserCreate
from app.wireguard_manager.database import Base, engine
from app.api.routes import servers, peers, gui


async def create_db_and_tables():
    async with engine.begin() as conn:  # type: ignore[attr-defined]
        await conn.run_sync(Base.metadata.create_all)


app = create_app()


@app.on_event("startup")
async def _startup():
    await create_db_and_tables()


api_router = APIRouter(prefix="/api")
api_router.include_router(servers.router)
api_router.include_router(peers.router)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)

app.include_router(api_router)
app.include_router(gui.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


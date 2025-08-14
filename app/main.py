"""ASGI entrypoint (refactored).

Business logic & routes moved to modular packages under app/.
"""
from __future__ import annotations

from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
from app.core.config import create_app
from app.users.users import fastapi_users, auth_backend
from app.users.db import get_user_db
from app.users.users import get_user_manager
from app.users.schemas import UserCreate as _UserCreateSchema
from app.users.schemas import UserRead, UserCreate
from app.wireguard_manager.database import Base, engine
from app.api.routes import servers, peers, gui, auth_extra


async def create_db_and_tables():
    async with engine.begin() as conn:  # type: ignore[attr-defined]
        await conn.run_sync(Base.metadata.create_all)


app = create_app()


@app.on_event("startup")
async def _startup():
    await create_db_and_tables()
    # Create default admin user if it doesn't exist
    async def ensure_admin():
        from app.wireguard_manager.database import SessionLocal  # type: ignore
        async with SessionLocal() as session:  # type: ignore
            user_db_dep = get_user_db(session)
            user_db = None
            async for udb in user_db_dep:  # dependency generator pattern
                user_db = udb
            if user_db is None:
                return
            existing = await user_db.get_by_email("admin@firewallo.io")  # fastapi-users uses email field
            if existing:
                return
            user_manager_dep = get_user_manager(user_db)
            user_manager = None
            async for um in user_manager_dep:  # generator pattern
                user_manager = um
            if user_manager is None:
                return
            user_create = _UserCreateSchema(email="admin@firewallo.io", password="admin", is_active=True, is_superuser=True, is_verified=True)
            try:
                await user_manager.create(user_create)
                print("[startup] Created default admin user (email=admin@firewallo.io / password=admin)")
            except ValueError as exc:  # pragma: no cover - defensive
                print(f"[startup] Could not create admin user: {exc}")
    await ensure_admin()


api_router = APIRouter(prefix="/api")
api_router.include_router(servers.router)
api_router.include_router(peers.router)
api_router.include_router(auth_extra.router)

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


from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from app.users.db import get_user_db
from app.wireguard_manager.models import User


SECRET = "SECRET"


# NOTE:
#   Original code mixed UUIDIDMixin with an integer primary key model (User.id -> int),
#   producing a runtime mismatch for fastapi-users generic parameters. Reverting to
#   a plain BaseUserManager with correct type parameter (int) fixes registration/login.
class UserManager(BaseUserManager[User, int]):
    # Override to ensure string IDs are converted to int. Signature must keep parameter name 'id'
    # to satisfy the abstract base method in fastapi-users.
    def parse_id(self, id):  # type: ignore[override]
        if isinstance(id, int):  # noqa: A003 - shadowing builtin acceptable here per base class contract
            return id
        try:
            return int(id)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid user id") from exc
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

async def get_user_manager(user_db = Depends(get_user_db)):
    yield UserManager(user_db)

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

# Updated to reflect the /api prefix for API endpoints
bearer_transport = BearerTransport(tokenUrl="/api/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)


"""Simple authentication models and utilities."""
from __future__ import annotations

import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from pathlib import Path

import jwt
from fastapi import HTTPException, status, Request
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

if TYPE_CHECKING:
        from typing import Dict, Any
        UserDoc = Dict[str, Any]


# JWT configuration
def get_secret_key() -> str:
    """Get or create persistent SECRET_KEY."""
    # Try environment variable first
    env_key = os.getenv("JWT_SECRET_KEY")
    if env_key:
        return env_key

    # Try to load from file
    secret_file = Path("data/core/jwt_secret.key")
    if secret_file.exists():
        try:
            with open(secret_file, 'r') as f:
                return f.read().strip()
        except Exception:
            pass

    # Generate new key and save it
    new_key = secrets.token_urlsafe(32)
    try:
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        with open(secret_file, 'w') as f:
            f.write(new_key)
    except Exception:
        pass  # Fallback to in-memory key

    return new_key

SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@dataclass
class UserData:
    """User data model for authentication."""
    email: str
    username: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[str] = None


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Security scheme
security = HTTPBearer()


async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Get the current authenticated user from JWT token."""
    from app.core.startup import CoreUserRepository

    user_repo = CoreUserRepository()

    payload = verify_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_repo.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get the current authenticated user from session or token."""
    from app.auth.sessions import get_session_manager
    from app.core.startup import CoreUserRepository

    session_manager = get_session_manager()
    user_repo = CoreUserRepository()

    # Method 1: Check session cookie first (preferred for web interface)
    session_id = request.cookies.get("session_id")
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            # Validate session security
            current_ip = getattr(request.client, 'host', None) if request.client else None
            current_ua = request.headers.get('User-Agent')

            if session_manager.validate_session_security(session, current_ip, current_ua):
                user_data = session.get('user_data')
                if user_data:
                    return user_data

    # Method 2: Check Authorization header for API access
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = verify_token(token)
            username = payload.get("sub")
            if username:
                user = user_repo.get_user_by_username(username)
                if user:
                    return user
        except HTTPException:
            pass

    # Method 3: Check access_token cookie for compatibility
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = verify_token(access_token)
            username = payload.get("sub")
            if username:
                user = user_repo.get_user_by_username(username)
                if user:
                    return user
        except HTTPException:
            pass

    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


class User:
    """User model for compatibility with existing code."""

    def __init__(self, user_data: Dict[str, Any]):
        self.username = user_data.get("username", "")
        self.email = user_data.get("email", "")
        self.is_active = user_data.get("is_active", False)
        self.is_superuser = user_data.get("is_superuser", False)
        self.first_name = user_data.get("first_name", "")
        self.last_name = user_data.get("last_name", "")
        self.role = user_data.get("role", "user")
        self.created_at = user_data.get("created_at", "")
        self.hashed_password = user_data.get("hashed_password", "")


# Compatibility functions
async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Dependency for API endpoints that require token-based auth."""
    return await get_current_user_from_token(credentials)


async def current_active_user(request: Request) -> User:
    """Get current active user dependency for web interface."""
    user_data = await get_current_user(request)
    if not user_data.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return User(user_data)


async def current_active_user_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Get current active user dependency for API endpoints."""
    user_data = await get_current_user_from_token(credentials)
    if not user_data.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return User(user_data)

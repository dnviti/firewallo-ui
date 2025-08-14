"""Simple authentication models and utilities."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Depends, status
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

if TYPE_CHECKING:
        from typing import Dict, Any
        UserDoc = Dict[str, Any]


# JWT configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@dataclass
class User:
    """User model for authentication."""
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


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Get the current authenticated user."""
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


# Alias for compatibility with existing code
async def current_active_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Get current active user dependency."""
    user_data = await get_current_user(credentials)
    if not user_data.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return User(user_data)

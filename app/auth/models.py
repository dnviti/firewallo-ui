"""Simple authentication models and utilities."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

if TYPE_CHECKING:
        from app.plugins.wireguard.repository import UserDoc


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


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> "UserDoc":
    """Get the current authenticated user."""
    from app.plugins.wireguard.repository import repo
    
    payload = verify_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = repo.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Alias for compatibility with existing code
current_active_user = get_current_user

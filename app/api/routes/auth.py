"""Authentication routes."""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth.models import User, hash_password, verify_password, create_access_token
from app.plugins.wireguard.repository import repo, UserDoc


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserResponse(BaseModel):
    email: str
    username: str
    is_active: bool
    is_superuser: bool


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter(tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with username and password."""
    # Try to find user by username or email
    user = repo.get_user_by_username(form_data.username)
    if not user:
        user = repo.get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate):
    """Register a new user."""
    try:
        user_doc = UserDoc(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            created_at=datetime.now().isoformat(),
        )
        repo.create_user(user_doc)
        
        return UserResponse(
            email=user_doc.email,
            username=user_doc.username,
            is_active=user_doc.is_active,
            is_superuser=user_doc.is_superuser,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Legacy compatibility endpoints for existing frontend
@router.post("/jwt/login", response_model=Token)
def jwt_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Legacy JWT login endpoint for compatibility."""
    return login(form_data)

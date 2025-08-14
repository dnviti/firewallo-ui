"""Authentication routes."""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth.models import User, hash_password, verify_password, create_access_token
from app.core.startup import CoreUserRepository


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

# Initialize user repository
user_repo = CoreUserRepository()


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with username and password."""
    # Try to find user by username or email
    user = user_repo.get_user_by_username(form_data.username)
    if not user:
        user = user_repo.get_user_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.get("username")}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate):
    """Register a new user."""
    try:
        # Check if user already exists
        if user_repo.get_user_by_username(user_data.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        if user_repo.get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "hashed_password": hash_password(user_data.password),
            "is_active": True,
            "is_superuser": False,
            "first_name": "",
            "last_name": "",
            "role": "user"
        }

        success = user_repo.create_user(user_dict)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create user")

        return UserResponse(
            email=user_dict["email"],
            username=user_dict["username"],
            is_active=user_dict["is_active"],
            is_superuser=user_dict["is_superuser"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends()):
    """Get current user information."""
    # Convert User model to UserResponse
    return UserResponse(
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )


@router.get("/users")
def list_users():
    """List all users (admin only)."""
    try:
        users = user_repo.list_users()
        # Remove sensitive information
        safe_users = []
        for user in users:
            safe_user = {
                "username": user.get("username"),
                "email": user.get("email"),
                "is_active": user.get("is_active", False),
                "is_superuser": user.get("is_superuser", False),
                "created_at": user.get("created_at"),
                "role": user.get("role", "user")
            }
            safe_users.append(safe_user)

        return {"users": safe_users, "count": len(safe_users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


# Legacy compatibility endpoints for existing frontend
@router.post("/jwt/login", response_model=Token)
def jwt_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Legacy JWT login endpoint for compatibility."""
    return login(form_data)


@router.post("/token", response_model=Token)
def create_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Alternative token endpoint for compatibility."""
    return login(form_data)

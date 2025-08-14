from __future__ import annotations
from fastapi import APIRouter, Depends
from app.wireguard_manager import models
from app.users.users import current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
async def me(user: models.User = Depends(current_active_user)):
    return {"id": user.id, "email": user.email, "is_superuser": user.is_superuser, "is_verified": user.is_verified}

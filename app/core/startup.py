"""Application startup utilities."""
from __future__ import annotations

from datetime import datetime
from app.auth.models import hash_password
from app.wireguard_manager.repository import repo, UserDoc


def create_default_admin() -> None:
    """Create default admin user if it doesn't exist."""
    try:
        # Check if admin user already exists
        existing = repo.get_user_by_username("admin")
        if existing:
            print("[startup] Admin user already exists")
            return
        
        # Create default admin user
        admin_user = UserDoc(
            email="admin@firewallo.io",
            username="admin", 
            hashed_password=hash_password("admin"),
            is_active=True,
            is_superuser=True,
            created_at=datetime.now().isoformat()
        )
        
        repo.create_user(admin_user)
        print("[startup] Created default admin user (username=admin / password=admin)")
        
    except Exception as exc:
        print(f"[startup] Could not create admin user: {exc}")

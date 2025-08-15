"""Application startup utilities."""
from __future__ import annotations

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from app.auth.models import hash_password

logger = logging.getLogger("firewallo.startup")


class CoreUserRepository:
    """Core user repository that doesn't depend on plugins."""

    def __init__(self):
        self.users_file = Path("data/core/users.json")
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_users_file()

    def _ensure_users_file(self):
        """Ensure users file exists with proper structure."""
        if not self.users_file.exists():
            default_data = {
                "users": [],
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
            with open(self.users_file, 'w') as f:
                json.dump(default_data, f, indent=2)

    def _load_users(self) -> Dict[str, Any]:
        """Load users data from file."""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load users file: {e}")
            return {"users": [], "created_at": datetime.utcnow().isoformat(), "version": "1.0.0"}

    def _save_users(self, data: Dict[str, Any]) -> bool:
        """Save users data to file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save users file: {e}")
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        data = self._load_users()
        for user in data.get("users", []):
            if user.get("username") == username:
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        data = self._load_users()
        for user in data.get("users", []):
            if user.get("email") == email:
                return user
        return None

    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user."""
        try:
            data = self._load_users()

            # Check if user already exists
            if self.get_user_by_username(user_data.get("username", "")):
                return False
            if self.get_user_by_email(user_data.get("email", "")):
                return False

            # Add user with metadata
            user_record = {
                **user_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            data["users"].append(user_record)
            return self._save_users(data)

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def list_users(self) -> list:
        """List all users."""
        data = self._load_users()
        return data.get("users", [])


def create_default_admin() -> None:
    """Create default admin user if it doesn't exist."""
    try:
        # Initialize core user repository
        user_repo = CoreUserRepository()

        # Check if admin user already exists
        existing = user_repo.get_user_by_username("admin")
        if existing:
            logger.info("Admin user already exists")
            return

        # Create default admin user
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@firewallo.io")

        admin_user = {
            "email": admin_email,
            "username": "admin",
            "hashed_password": hash_password(admin_password),
            "is_active": True,
            "is_superuser": True,
            "first_name": "Administrator",
            "last_name": "",
            "role": "admin"
        }

        success = user_repo.create_user(admin_user)
        if success:
            logger.info(f"Created default admin user (username=admin, email={admin_email})")
            if admin_password == "admin":
                logger.warning("Using default admin password 'admin' - please change this in production!")
        else:
            logger.error("Failed to create default admin user")

    except Exception as exc:
        logger.error(f"Could not create admin user: {exc}")


def initialize_core_data() -> None:
    """Initialize core application data directories and files."""
    try:
        # Create core data directories
        core_dirs = [
            "data/core",
            "data/plugins",
            "data/logs",
            "data/backups",
            "data/temp"
        ]

        for dir_path in core_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Create core configuration if it doesn't exist
        core_config_file = Path("data/core/config.json")
        if not core_config_file.exists():
            default_config = {
                "application": {
                    "name": "Firewallo",
                    "version": "1.0.0",
                    "environment": os.getenv("ENVIRONMENT", "development")
                },
                "features": {
                    "plugins_enabled": True,
                    "hot_reload": True,
                    "auto_discovery": True
                },
                "security": {
                    "require_auth": True,
                    "session_timeout": 3600,
                    "max_login_attempts": 5
                },
                "created_at": datetime.utcnow().isoformat()
            }

            with open(core_config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

            logger.info("Created core configuration file")

        logger.info("Core data initialization completed")

    except Exception as exc:
        logger.error(f"Failed to initialize core data: {exc}")


def startup_checks() -> bool:
    """Perform startup health checks."""
    try:
        checks_passed = True

        # Check data directory permissions
        data_dir = Path("data")
        if not data_dir.exists():
            logger.error("Data directory does not exist")
            checks_passed = False
        elif not os.access(data_dir, os.W_OK):
            logger.error("Data directory is not writable")
            checks_passed = False

        # Check core files
        core_files = ["data/core/users.json", "data/core/config.json"]
        for file_path in core_files:
            if not Path(file_path).exists():
                logger.warning(f"Core file missing: {file_path}")

        # Check environment variables
        required_env_vars = []  # Add any required environment variables
        for env_var in required_env_vars:
            if not os.getenv(env_var):
                logger.error(f"Required environment variable not set: {env_var}")
                checks_passed = False

        if checks_passed:
            logger.info("All startup checks passed")
        else:
            logger.warning("Some startup checks failed")

        return checks_passed

    except Exception as exc:
        logger.error(f"Startup checks failed: {exc}")
        return False


def run_startup_tasks() -> None:
    """Run all startup tasks in order."""
    logger.info("Running startup tasks...")

    try:
        # 1. Initialize core data
        initialize_core_data()

        # 2. Run startup checks
        startup_checks()

        # 3. Create default admin user
        create_default_admin()

        # 4. Cleanup expired sessions
        cleanup_expired_sessions()

        logger.info("Startup tasks completed successfully")

    except Exception as exc:
        logger.error(f"Startup tasks failed: {exc}")
        raise


# Compatibility function for existing code
def cleanup_expired_sessions() -> None:
    """Cleanup expired sessions on startup."""
    try:
        from app.auth.sessions import cleanup_sessions_on_startup
        cleanup_sessions_on_startup()
        logger.info("Session cleanup completed")
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")


def create_default_admin_user():
    """Alias for create_default_admin for backward compatibility."""
    create_default_admin()

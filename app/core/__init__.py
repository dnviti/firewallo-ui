"""Core application utilities (app factory, configuration, startup)."""
from .config import create_app  # noqa: F401
from . import startup  # noqa: F401

__all__ = ["create_app", "startup"]

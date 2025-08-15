"""Plugin dependencies for FastAPI routes.

This module provides dependency functions that can be used to protect plugin routes
and ensure plugins are enabled before allowing access to their functionality.
"""

from fastapi import HTTPException, status, Depends
from typing import Callable, Optional
import logging

logger = logging.getLogger("firewallo.plugins.dependencies")


def create_plugin_enabled_dependency(plugin_name: str, category: str) -> Callable:
    """Create a dependency function that checks if a specific plugin is enabled.

    Args:
        plugin_name: Name of the plugin to check
        category: Category of the plugin

    Returns:
        Callable: Dependency function that raises HTTPException if plugin is disabled
    """
    def check_plugin_enabled():
        """Check if the specified plugin is enabled."""
        plugin_path = f"{category}.{plugin_name}"

        try:
            from app.plugins.registry import plugin_manager

            # Check if plugin is loaded and enabled
            if not plugin_manager.is_plugin_loaded(plugin_path):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Plugin '{plugin_name}' is not loaded"
                )

            if not plugin_manager.is_plugin_enabled(plugin_path):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Plugin '{plugin_name}' is currently disabled"
                )

        except ImportError:
            logger.warning(f"Plugin manager not available, cannot check status for {plugin_name}")
            # If plugin manager is not available, we allow access
            # This is for development/testing scenarios
            pass
        except Exception as e:
            logger.error(f"Error checking plugin status for {plugin_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Plugin '{plugin_name}' status check failed"
            )

    return check_plugin_enabled


def create_plugin_dependency(plugin_instance) -> Callable:
    """Create a dependency function that checks if a plugin instance is enabled.

    Args:
        plugin_instance: The plugin instance to check

    Returns:
        Callable: Dependency function that raises HTTPException if plugin is disabled
    """
    def check_plugin_enabled():
        """Check if the plugin instance is enabled."""
        try:
            plugin_path = f"{plugin_instance.category}.{plugin_instance.name}"

            from app.plugins.registry import plugin_manager

            # Check if plugin is enabled in the plugin manager
            if not plugin_manager.is_plugin_enabled(plugin_path):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Plugin '{plugin_instance.name}' is currently disabled"
                )

        except ImportError:
            # Fallback to checking the plugin instance's enabled flag
            if not getattr(plugin_instance, 'enabled', True):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Plugin '{plugin_instance.name}' is currently disabled"
                )
        except Exception as e:
            logger.error(f"Error checking plugin status: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Plugin '{plugin_instance.name}' status check failed"
            )

    return check_plugin_enabled


def require_plugin_enabled(plugin_name: str, category: str):
    """Dependency that requires a specific plugin to be enabled.

    Usage:
        @router.get("/some-route")
        async def my_route(
            _enabled: None = Depends(require_plugin_enabled("wireguard", "vpn"))
        ):
            # Route logic here

    Args:
        plugin_name: Name of the plugin
        category: Category of the plugin
    """
    return Depends(create_plugin_enabled_dependency(plugin_name, category))


def require_plugin_instance_enabled(plugin_instance):
    """Dependency that requires a plugin instance to be enabled.

    Usage:
        @router.get("/some-route")
        async def my_route(
            _enabled: None = Depends(require_plugin_instance_enabled(self.plugin))
        ):
            # Route logic here

    Args:
        plugin_instance: The plugin instance
    """
    return Depends(create_plugin_dependency(plugin_instance))


class PluginMiddleware:
    """Middleware class for plugin route protection.

    This can be used as an alternative to dependency injection for protecting
    entire routers or groups of routes.
    """

    def __init__(self, plugin_name: str, category: str):
        """Initialize the middleware.

        Args:
            plugin_name: Name of the plugin
            category: Category of the plugin
        """
        self.plugin_name = plugin_name
        self.category = category
        self.plugin_path = f"{category}.{plugin_name}"

    async def __call__(self, request, call_next):
        """Middleware function to check plugin status.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response: Either an error response or the result of call_next
        """
        try:
            from app.plugins.registry import plugin_manager

            if not plugin_manager.is_plugin_enabled(self.plugin_path):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "detail": f"Plugin '{self.plugin_name}' is currently disabled"
                    }
                )

        except ImportError:
            # If plugin manager is not available, allow the request
            logger.warning(f"Plugin manager not available for middleware check: {self.plugin_name}")
        except Exception as e:
            logger.error(f"Error in plugin middleware for {self.plugin_name}: {e}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": f"Plugin '{self.plugin_name}' status check failed"
                }
            )

        # Plugin is enabled or check failed gracefully, continue with request
        response = await call_next(request)
        return response

"""Base plugin class for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import uuid
from datetime import datetime
from pathlib import Path

from .exceptions import PluginError, PluginConfigurationError


class BasePlugin(ABC):
    """Base class for all Firewallo plugins.

    All plugins must inherit from this class and implement the abstract methods.
    This provides a consistent interface for plugin management and operation.
    """

    def __init__(self):
        """Initialize the base plugin."""
        self.name: str = ""
        self.category: str = ""
        self.version: str = ""
        self.description: str = ""
        self.author: str = ""
        self.license: str = ""
        self.enabled: bool = True
        self.config: Dict[str, Any] = {}
        self.manifest: Dict[str, Any] = {}
        self.plugin_id: str = str(uuid.uuid4())
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

        # Web UI properties
        self.webui_enabled: bool = False
        self.webui_router: Optional[APIRouter] = None
        self.webui_handler: Optional[Any] = None
        self.webui_templates: Optional[Jinja2Templates] = None
        self.webui_base_path: str = ""
        self.webui_static_mounted: bool = False
        self.menu_entry_registered: bool = False

        # Setup logger for this plugin
        self.logger = logging.getLogger(f"firewallo.plugins.{self.category}.{self.name}")

        # Plugin state
        self._initialized: bool = False
        self._startup_time: Optional[datetime] = None
        self._shutdown_time: Optional[datetime] = None
        self._error_count: int = 0
        self._last_error: Optional[str] = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin.

        This method is called when the plugin is loaded and should perform
        any necessary setup operations like connecting to external services,
        validating configuration, or preparing resources.

        Returns:
            bool: True if initialization was successful, False otherwise.

        Raises:
            PluginInitializationError: If initialization fails.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup plugin resources.

        This method is called when the plugin is unloaded and should perform
        any necessary cleanup operations like closing connections, releasing
        resources, or saving state.

        Raises:
            PluginShutdownError: If shutdown fails.
        """
        pass

    @abstractmethod
    def get_api_routes(self) -> List[APIRouter]:
        """Return FastAPI routers for this plugin.

        Returns:
            List[APIRouter]: List of FastAPI routers that define the plugin's API endpoints.
        """
        pass

    @abstractmethod
    def get_database_schema(self) -> Dict[str, Any]:
        """Return the database schema for this plugin.

        This defines the structure of data that the plugin will store in the database.
        The schema should follow the plugin's namespace pattern.

        Returns:
            Dict[str, Any]: Database schema definition for this plugin.
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.

        Override this method to implement custom configuration validation.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            bool: True if configuration is valid, False otherwise.

        Raises:
            PluginConfigurationError: If configuration is invalid.
        """
        try:
            # Basic validation - check required fields from manifest
            if not self.manifest:
                return True

            required_config = self.manifest.get('configuration', {}).get('required', [])
            for field in required_config:
                if field not in config:
                    raise PluginConfigurationError(
                        f"Required configuration field '{field}' is missing",
                        plugin_name=self.name
                    )

            return True
        except Exception as e:
            if isinstance(e, PluginConfigurationError):
                raise
            raise PluginConfigurationError(
                f"Configuration validation failed: {str(e)}",
                plugin_name=self.name
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Return plugin health information.

        Returns:
            Dict[str, Any]: Health status information including status, uptime, errors, etc.
        """
        uptime = None
        if self._startup_time:
            uptime = (datetime.utcnow() - self._startup_time).total_seconds()

        status = "healthy"
        if not self.enabled:
            status = "disabled"
        elif not self._initialized:
            status = "not_initialized"
        elif self._error_count > 0:
            status = "degraded"

        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "status": status,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "uptime_seconds": uptime,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "startup_time": self._startup_time.isoformat() if self._startup_time else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Return plugin metrics.

        Override this method to provide custom metrics for monitoring.

        Returns:
            Dict[str, Any]: Plugin-specific metrics.
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "error_count": self._error_count,
            "uptime_seconds": (datetime.utcnow() - self._startup_time).total_seconds()
                            if self._startup_time else 0
        }

    def get_info(self) -> Dict[str, Any]:
        """Return basic plugin information.

        Returns:
            Dict[str, Any]: Basic plugin metadata and information.
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "api_prefix": self.manifest.get('api_prefix', f"/api/{self.category}/{self.name}"),
            "database_path": self.manifest.get('database_path', f"plugins.{self.category}.{self.name}"),
            "supports_hot_reload": self.manifest.get('supports_hot_reload', False),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set plugin configuration after validation.

        Args:
            config: Configuration dictionary to set.

        Raises:
            PluginConfigurationError: If configuration is invalid.
        """
        if self.validate_config(config):
            self.config = config.copy()
            self.updated_at = datetime.utcnow()
            self.logger.info(f"Configuration updated for plugin {self.name}")

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update specific configuration values.

        Args:
            updates: Dictionary of configuration updates to apply.

        Raises:
            PluginConfigurationError: If updated configuration is invalid.
        """
        new_config = self.config.copy()
        new_config.update(updates)
        self.set_config(new_config)

    def get_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value(s).

        Args:
            key: Specific configuration key to retrieve. If None, returns entire config.
            default: Default value to return if key is not found.

        Returns:
            Any: Configuration value(s).
        """
        if key is None:
            return self.config.copy()
        return self.config.get(key, default)

    def set_manifest(self, manifest: Dict[str, Any]) -> None:
        """Set plugin manifest data.

        Args:
            manifest: Plugin manifest dictionary.
        """
        self.manifest = manifest.copy()

        # Update basic plugin info from manifest
        self.name = manifest.get('name', self.name)
        self.category = manifest.get('category', self.category)
        self.version = manifest.get('version', self.version)
        self.description = manifest.get('description', self.description)
        self.author = manifest.get('author', self.author)
        self.license = manifest.get('license', self.license)

        self.updated_at = datetime.utcnow()

        # Initialize Web UI if configured
        if manifest.get('webui', {}).get('enabled', False):
            self.webui_enabled = True
            self.webui_base_path = manifest['webui']['routes'].get(
                'base_path',
                f"/plugins/{self.category}/{self.name}"
            )

    async def initialize_webui(self) -> bool:
        """Initialize plugin web UI components.

        Returns:
            bool: True if WebUI initialization was successful, False otherwise.
        """
        if not self.webui_enabled:
            return False

        try:
            # Check if webui module exists
            webui_module_path = Path(__file__).parent.parent / self.category / self.name / "webui"
            if not webui_module_path.exists():
                self.logger.warning(f"WebUI enabled but webui directory not found for {self.name}")
                return False

            # Try to import WebUI handler
            try:
                import importlib
                webui_module = importlib.import_module(
                    f"app.plugins.{self.category}.{self.name}.webui.routes"
                )

                # Get the WebUI class (convention: PluginWebUI or {Name}WebUI)
                webui_class = None
                for attr_name in ['PluginWebUI', f'{self.name.title()}WebUI', 'WebUI']:
                    if hasattr(webui_module, attr_name):
                        webui_class = getattr(webui_module, attr_name)
                        break

                if webui_class:
                    self.webui_handler = webui_class(self)
                    self.webui_router = self.webui_handler.router
                else:
                    # Fallback to get_webui_router function if exists
                    if hasattr(webui_module, 'get_webui_router'):
                        self.webui_router = webui_module.get_webui_router(self)
                    else:
                        self.logger.warning(f"No WebUI handler found for {self.name}")
                        return False

            except ImportError as e:
                self.logger.warning(f"Could not import WebUI module for {self.name}: {e}")
                return False

            # Setup templates if template path is specified
            template_path = self.manifest.get('webui', {}).get('template_path')
            if template_path:
                full_template_path = Path(__file__).parent.parent / self.category / self.name / template_path
                if full_template_path.exists():
                    self.webui_templates = Jinja2Templates(directory=str(full_template_path))

            # Register menu entry
            await self.register_menu_entry()

            # Mount static files will be done by the main app
            # We just prepare the path here
            static_path = self.manifest.get('webui', {}).get('static_path')
            if static_path:
                self.webui_static_path = Path(__file__).parent.parent / self.category / self.name / static_path
            else:
                self.webui_static_path = None

            self.logger.info(f"WebUI initialized successfully for {self.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize WebUI for {self.name}: {e}")
            return False

    async def register_menu_entry(self) -> bool:
        """Register plugin menu entry in the main navigation.

        Returns:
            bool: True if menu registration was successful, False otherwise.
        """
        if not self.webui_enabled:
            self.logger.debug(f"Menu registration skipped for {self.name}: WebUI not enabled")
            return False

        if self.menu_entry_registered:
            self.logger.debug(f"Menu registration skipped for {self.name}: Already registered")
            return False

        try:
            menu_config = self.manifest.get('webui', {}).get('menu_entry', {})
            self.logger.info(f"Registering menu entry for {self.name} with config: {menu_config}")

            menu_entry = {
                'id': f"{self.category}_{self.name}",
                'title': menu_config.get('title', self.name.title()),
                'icon': menu_config.get('icon', 'bi-puzzle'),
                'url': self.webui_base_path,
                'category': self.category,
                'position': menu_config.get('position', 999),
                'permissions': menu_config.get('permissions', []),
                'badge': None,
                'active': self.enabled,
                'visible': True
            }

            self.logger.info(f"Menu entry prepared for {self.name}: {menu_entry}")

            # Try to register with menu service if available
            try:
                from app.plugins.system.webui.services import MenuService

                # Initialize MenuService if not already done
                if not hasattr(MenuService, '_repository') or MenuService._repository is None:
                    await MenuService.initialize()
                    self.logger.info("MenuService initialized")

                result = await MenuService.register_plugin_menu(menu_entry)
                if result:
                    self.menu_entry_registered = True
                    self.logger.info(f"✅ Menu entry successfully registered for {self.name}")
                    return True
                else:
                    self.logger.error(f"❌ Menu entry registration failed for {self.name}")
                    return False

            except ImportError as e:
                self.logger.warning(f"MenuService not available: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Error during menu registration: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to register menu entry for {self.name}: {e}")
            return False

    async def update_menu_badge(self, count: Optional[int] = None, style: str = "primary") -> bool:
        """Update the menu entry badge for this plugin.

        Args:
            count: Badge count to display. None removes the badge.
            style: Bootstrap badge style (primary, secondary, success, danger, warning, info)

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not self.menu_entry_registered:
            return False

        try:
            from app.plugins.system.webui.services import MenuService
            menu_id = f"{self.category}_{self.name}"
            return await MenuService.update_badge(menu_id, count, style)
        except Exception as e:
            self.logger.error(f"Failed to update menu badge: {e}")
            return False

    async def set_menu_visibility(self, visible: bool) -> bool:
        """Set the visibility of the plugin's menu entry.

        Args:
            visible: Whether the menu entry should be visible.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not self.menu_entry_registered:
            return False

        try:
            from app.plugins.system.webui.services import MenuService
            menu_id = f"{self.category}_{self.name}"
            return await MenuService.set_visibility(menu_id, visible)
        except Exception as e:
            self.logger.error(f"Failed to update menu visibility: {e}")
            return False

    async def update_menu_title(self, title: str) -> bool:
        """Update the menu entry title for this plugin.

        Args:
            title: New title for the menu entry.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not self.menu_entry_registered:
            return False

        try:
            from app.plugins.system.webui.services import MenuService
            menu_id = f"{self.category}_{self.name}"
            return await MenuService.update_title(menu_id, title)
        except Exception as e:
            self.logger.error(f"Failed to update menu title: {e}")
            return False

    async def unregister_menu_entry(self) -> bool:
        """Unregister plugin menu entry from the main navigation.

        Returns:
            bool: True if menu unregistration was successful, False otherwise.
        """
        if not self.menu_entry_registered:
            self.logger.debug(f"Menu unregistration skipped for {self.name}: no menu entry registered")
            return True

        try:
            from app.plugins.system.webui.services import MenuService
            menu_id = f"{self.category}_{self.name}"

            result = await MenuService.unregister_plugin_menu(menu_id)
            if result:
                self.menu_entry_registered = False
                self.logger.info(f"✅ Menu entry successfully unregistered for {self.name}")
                return True
            else:
                self.logger.error(f"❌ Menu entry unregistration failed for {self.name}")
                return False

        except ImportError as e:
            self.logger.warning(f"MenuService not available: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error during menu unregistration: {e}")
            return False

    def check_plugin_enabled(self) -> None:
        """Check if plugin is enabled and raise HTTPException if not.

        This method can be used as a FastAPI dependency to protect plugin routes.

        Raises:
            HTTPException: 503 Service Unavailable if plugin is disabled
        """
        # Check both the plugin's enabled flag and the plugin manager's enabled plugins
        plugin_path = f"{self.category}.{self.name}"

        # Try to get plugin manager and check if plugin is enabled
        try:
            from app.plugins.registry import plugin_manager
            if not plugin_manager.is_plugin_enabled(plugin_path):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Plugin '{self.name}' is currently disabled"
                )
        except ImportError:
            # Fallback to local enabled flag if plugin manager not available
            if not self.enabled:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Plugin '{self.name}' is currently disabled"
                )

    def get_webui_info(self) -> Dict[str, Any]:
        """Get WebUI configuration and status information.

        Returns:
            Dict[str, Any]: WebUI information including paths, status, and configuration.
        """
        return {
            "enabled": self.webui_enabled,
            "base_path": self.webui_base_path,
            "has_router": self.webui_router is not None,
            "has_templates": self.webui_templates is not None,
            "static_mounted": self.webui_static_mounted,
            "menu_registered": self.menu_entry_registered,
            "use_system_theme": self.manifest.get('webui', {}).get('routes', {}).get('use_system_theme', True),
            "static_path": f"{self.webui_base_path}/static" if self.webui_static_mounted else None
        }

    def get_webui_routes(self) -> Optional[APIRouter]:
        """Get the WebUI router for this plugin.

        Returns:
            Optional[APIRouter]: The WebUI router if available, None otherwise.
        """
        return self.webui_router

    def log_error(self, error: str, exception: Optional[Exception] = None) -> None:
        """Log an error and update error tracking.

        Args:
            error: Error message to log.
            exception: Optional exception object for additional context.
        """
        self._error_count += 1
        self._last_error = error
        self.updated_at = datetime.utcnow()

        if exception:
            self.logger.error(f"{error}: {str(exception)}", exc_info=exception)
        else:
            self.logger.error(error)

    def mark_initialized(self) -> None:
        """Mark the plugin as successfully initialized."""
        self._initialized = True
        self._startup_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.logger.info(f"Plugin {self.name} initialized successfully")

        # Initialize WebUI if enabled
        if self.webui_enabled:
            self.logger.info(f"WebUI enabled for {self.name}, scheduling initialization")
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self.initialize_webui())
                # Also schedule menu registration
                asyncio.create_task(self.register_menu_entry())
            else:
                loop.run_until_complete(self.initialize_webui())
                loop.run_until_complete(self.register_menu_entry())

    def mark_shutdown(self) -> None:
        """Mark the plugin as shut down."""
        self._initialized = False
        self._shutdown_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.logger.info(f"Plugin {self.name} shut down successfully")

    def __str__(self) -> str:
        """String representation of the plugin."""
        return f"{self.category}.{self.name} v{self.version}"

    def __repr__(self) -> str:
        """Detailed string representation of the plugin."""
        return (f"<{self.__class__.__name__}(name={self.name}, category={self.category}, "
                f"version={self.version}, enabled={self.enabled}, initialized={self._initialized})>")

"""Base plugin class for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from fastapi import APIRouter
import logging
import uuid
from datetime import datetime

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

"""Common interfaces for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Generic, TypeVar
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

# Type variables for generic interfaces
T = TypeVar('T')
CreateT = TypeVar('CreateT', bound=BaseModel)
ResponseT = TypeVar('ResponseT', bound=BaseModel)
UpdateT = TypeVar('UpdateT', bound=BaseModel)


class PluginInterface(ABC):
    """Base interface that all plugins must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name identifier."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Plugin category (vpn, firewall, monitoring, etc.)."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string."""
        pass


class ConfigurableInterface(ABC):
    """Interface for plugins that support configuration management."""

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        pass

    @abstractmethod
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set plugin configuration."""
        pass

    @abstractmethod
    def get_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value(s)."""
        pass


class HealthCheckInterface(ABC):
    """Interface for plugins that support health checking."""

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get plugin health status."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get plugin metrics."""
        pass


class APIProviderInterface(ABC):
    """Interface for plugins that provide API endpoints."""

    @abstractmethod
    def get_api_routes(self) -> List[APIRouter]:
        """Get FastAPI routers for this plugin."""
        pass

    @property
    @abstractmethod
    def api_prefix(self) -> str:
        """Get API prefix for this plugin."""
        pass


class DatabaseInterface(ABC):
    """Interface for plugins that interact with the database."""

    @abstractmethod
    def get_database_schema(self) -> Dict[str, Any]:
        """Get database schema definition."""
        pass

    @property
    @abstractmethod
    def database_path(self) -> str:
        """Get database path for this plugin."""
        pass


class LifecycleInterface(ABC):
    """Interface for plugin lifecycle management."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    @abstractmethod
    async def reload(self) -> bool:
        """Reload the plugin configuration/state."""
        pass


class CRUDInterface(Generic[CreateT, ResponseT, UpdateT], ABC):
    """Generic CRUD interface for plugin resources."""

    @abstractmethod
    async def create(self, data: CreateT) -> ResponseT:
        """Create a new resource."""
        pass

    @abstractmethod
    async def get(self, resource_id: str) -> Optional[ResponseT]:
        """Get a resource by ID."""
        pass

    @abstractmethod
    async def list(self, **filters) -> List[ResponseT]:
        """List resources with optional filtering."""
        pass

    @abstractmethod
    async def update(self, resource_id: str, data: UpdateT) -> Optional[ResponseT]:
        """Update an existing resource."""
        pass

    @abstractmethod
    async def delete(self, resource_id: str) -> bool:
        """Delete a resource."""
        pass


class RepositoryInterface(Generic[T], ABC):
    """Base repository interface for data access."""

    @abstractmethod
    async def get_data(self, path: str) -> Optional[Dict[str, Any]]:
        """Get data from storage path."""
        pass

    @abstractmethod
    async def set_data(self, path: str, data: Dict[str, Any]) -> bool:
        """Set data at storage path."""
        pass

    @abstractmethod
    async def delete_data(self, path: str) -> bool:
        """Delete data at storage path."""
        pass

    @abstractmethod
    async def list_data(self, path: str) -> List[str]:
        """List data keys under path."""
        pass


class EventInterface(ABC):
    """Interface for plugins that handle events."""

    @abstractmethod
    async def on_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle an event."""
        pass

    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """Get list of supported event types."""
        pass


class ValidationInterface(ABC):
    """Interface for plugins that provide validation."""

    @abstractmethod
    def validate_data(self, data: Dict[str, Any], schema_name: str) -> bool:
        """Validate data against a schema."""
        pass

    @abstractmethod
    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        pass


class LoggingInterface(ABC):
    """Interface for plugins that provide logging capabilities."""

    @abstractmethod
    def log_info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message."""
        pass


class SecurityInterface(ABC):
    """Interface for plugins that handle security operations."""

    @abstractmethod
    def check_permissions(self, operation: str, resource: Optional[str] = None) -> bool:
        """Check if operation is permitted."""
        pass

    @abstractmethod
    def get_required_permissions(self) -> List[str]:
        """Get list of required permissions."""
        pass


class MonitoringInterface(ABC):
    """Interface for plugins that provide monitoring capabilities."""

    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect plugin metrics."""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get current status."""
        pass


class BackupInterface(ABC):
    """Interface for plugins that support backup/restore operations."""

    @abstractmethod
    async def backup_data(self) -> Dict[str, Any]:
        """Create a backup of plugin data."""
        pass

    @abstractmethod
    async def restore_data(self, backup_data: Dict[str, Any]) -> bool:
        """Restore plugin data from backup."""
        pass

    @abstractmethod
    def get_backup_info(self) -> Dict[str, Any]:
        """Get backup metadata information."""
        pass


class ScheduledInterface(ABC):
    """Interface for plugins that support scheduled operations."""

    @abstractmethod
    async def execute_scheduled_task(self, task_name: str) -> Dict[str, Any]:
        """Execute a scheduled task."""
        pass

    @abstractmethod
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of scheduled tasks."""
        pass


class NetworkInterface(ABC):
    """Interface for plugins that handle network operations."""

    @abstractmethod
    async def test_connectivity(self, target: str) -> Dict[str, Any]:
        """Test network connectivity to target."""
        pass

    @abstractmethod
    def get_network_status(self) -> Dict[str, Any]:
        """Get network status information."""
        pass


# Common data models for consistent API responses
class PluginInfo(BaseModel):
    """Standard plugin information model."""
    name: str
    category: str
    version: str
    description: str
    author: str
    license: str
    enabled: bool
    initialized: bool
    api_prefix: str
    database_path: str
    created_at: datetime
    updated_at: datetime


class PluginHealth(BaseModel):
    """Standard plugin health model."""
    name: str
    status: str  # healthy, degraded, unhealthy, disabled
    uptime_seconds: Optional[float]
    error_count: int
    last_error: Optional[str]
    last_check: datetime


class PluginMetrics(BaseModel):
    """Standard plugin metrics model."""
    name: str
    category: str
    enabled: bool
    initialized: bool
    uptime_seconds: float
    error_count: int
    custom_metrics: Dict[str, Any]
    collected_at: datetime


class PluginConfig(BaseModel):
    """Standard plugin configuration model."""
    plugin_name: str
    config_version: str
    required_fields: List[str]
    optional_fields: List[str]
    current_config: Dict[str, Any]
    updated_at: datetime


class PluginEvent(BaseModel):
    """Standard plugin event model."""
    event_id: str
    plugin_name: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    source: str

"""Base repository class for plugin data access."""

import json
import uuid
from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from pathlib import Path
import asyncio
import logging

from .exceptions import PluginDatabaseError
from .interfaces import RepositoryInterface

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository class for plugin data access.

    Provides common data access patterns for plugins including CRUD operations,
    configuration management, and data validation.
    """

    def __init__(self, plugin_name: str, category: str, database_path: Optional[str] = None):
        """Initialize the repository.

        Args:
            plugin_name: Name of the plugin.
            category: Category of the plugin.
            database_path: Optional custom database path.
        """
        self.plugin_name = plugin_name
        self.category = category
        self.database_path = database_path or f"plugins.{category}.{plugin_name}"
        self.logger = logging.getLogger(f"firewallo.plugins.{category}.{plugin_name}.repository")

        # In-memory cache for performance
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = True
        self._cache_ttl = 300  # 5 minutes default TTL
        self._cache_timestamps: Dict[str, datetime] = {}

    async def get_data(self, path: str, default: Optional[Any] = None) -> Optional[Any]:
        """Get data from storage path.

        Args:
            path: Data path relative to plugin namespace.
            default: Default value if path doesn't exist.

        Returns:
            Optional[Any]: Data at path or default.

        Raises:
            PluginDatabaseError: If data access fails.
        """
        try:
            full_path = f"{self.database_path}.{path}"

            # Check cache first
            if self._cache_enabled and self._is_cache_valid(full_path):
                return self._cache.get(full_path, default)

            # Load from database
            data = await self._load_from_database(full_path)

            if data is None:
                data = default

            # Update cache
            if self._cache_enabled:
                self._cache[full_path] = data
                self._cache_timestamps[full_path] = datetime.utcnow()

            return data

        except Exception as e:
            raise PluginDatabaseError(
                f"Failed to get data at path '{path}': {str(e)}",
                plugin_name=self.plugin_name
            )

    async def set_data(self, path: str, data: Any) -> bool:
        """Set data at storage path.

        Args:
            path: Data path relative to plugin namespace.
            data: Data to store.

        Returns:
            bool: True if successful.

        Raises:
            PluginDatabaseError: If data storage fails.
        """
        try:
            full_path = f"{self.database_path}.{path}"

            # Validate data is JSON serializable
            try:
                json.dumps(data, default=str)
            except (TypeError, ValueError) as e:
                raise PluginDatabaseError(
                    f"Data is not JSON serializable: {str(e)}",
                    plugin_name=self.plugin_name
                )

            # Save to database
            success = await self._save_to_database(full_path, data)

            if success:
                # Update cache
                if self._cache_enabled:
                    self._cache[full_path] = data
                    self._cache_timestamps[full_path] = datetime.utcnow()

                self.logger.debug(f"Stored data at path: {path}")
                return True

            return False

        except Exception as e:
            if isinstance(e, PluginDatabaseError):
                raise
            raise PluginDatabaseError(
                f"Failed to set data at path '{path}': {str(e)}",
                plugin_name=self.plugin_name
            )

    async def delete_data(self, path: str) -> bool:
        """Delete data at storage path.

        Args:
            path: Data path relative to plugin namespace.

        Returns:
            bool: True if successful.

        Raises:
            PluginDatabaseError: If data deletion fails.
        """
        try:
            full_path = f"{self.database_path}.{path}"

            # Delete from database
            success = await self._delete_from_database(full_path)

            if success:
                # Remove from cache
                if self._cache_enabled:
                    self._cache.pop(full_path, None)
                    self._cache_timestamps.pop(full_path, None)

                self.logger.debug(f"Deleted data at path: {path}")
                return True

            return False

        except Exception as e:
            if isinstance(e, PluginDatabaseError):
                raise
            raise PluginDatabaseError(
                f"Failed to delete data at path '{path}': {str(e)}",
                plugin_name=self.plugin_name
            )

    async def list_data(self, path: str = "") -> List[str]:
        """List data keys under path.

        Args:
            path: Base path to list under.

        Returns:
            List[str]: List of keys under the path.

        Raises:
            PluginDatabaseError: If listing fails.
        """
        try:
            full_path = f"{self.database_path}.{path}" if path else self.database_path
            return await self._list_from_database(full_path)

        except Exception as e:
            raise PluginDatabaseError(
                f"Failed to list data under path '{path}': {str(e)}",
                plugin_name=self.plugin_name
            )

    async def get_config(self, key: Optional[str] = None, default: Optional[Any] = None) -> Any:
        """Get plugin configuration.

        Args:
            key: Specific config key. If None, returns entire config.
            default: Default value if key doesn't exist.

        Returns:
            Any: Configuration value(s).
        """
        config_path = "config"
        if key:
            config_path = f"config.{key}"

        return await self.get_data(config_path, default)

    async def set_config(self, key: str, value: Any) -> bool:
        """Set plugin configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.

        Returns:
            bool: True if successful.
        """
        return await self.set_data(f"config.{key}", value)

    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values.

        Args:
            config_updates: Dictionary of configuration updates.

        Returns:
            bool: True if all updates were successful.
        """
        try:
            current_config = await self.get_config() or {}
            current_config.update(config_updates)
            return await self.set_data("config", current_config)
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False

    async def create_item(self, collection: str, item_data: Dict[str, Any], item_id: Optional[str] = None) -> str:
        """Create a new item in a collection.

        Args:
            collection: Collection name.
            item_data: Item data to store.
            item_id: Optional custom item ID. If None, generates UUID.

        Returns:
            str: ID of created item.

        Raises:
            PluginDatabaseError: If creation fails.
        """
        if item_id is None:
            item_id = self.generate_id()

        # Add metadata
        item_with_metadata = {
            **item_data,
            "id": item_id,
            "created_at": self.get_timestamp(),
            "updated_at": self.get_timestamp()
        }

        success = await self.set_data(f"{collection}.{item_id}", item_with_metadata)
        if not success:
            raise PluginDatabaseError(
                f"Failed to create item in collection '{collection}'",
                plugin_name=self.plugin_name
            )

        return item_id

    async def get_item(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item from a collection.

        Args:
            collection: Collection name.
            item_id: Item ID.

        Returns:
            Optional[Dict[str, Any]]: Item data if found.
        """
        return await self.get_data(f"{collection}.{item_id}")

    async def update_item(self, collection: str, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an item in a collection.

        Args:
            collection: Collection name.
            item_id: Item ID.
            updates: Update data.

        Returns:
            bool: True if successful.
        """
        item = await self.get_item(collection, item_id)
        if item is None:
            return False

        # Merge updates and update timestamp
        item.update(updates)
        item["updated_at"] = self.get_timestamp()

        return await self.set_data(f"{collection}.{item_id}", item)

    async def delete_item(self, collection: str, item_id: str) -> bool:
        """Delete an item from a collection.

        Args:
            collection: Collection name.
            item_id: Item ID.

        Returns:
            bool: True if successful.
        """
        return await self.delete_data(f"{collection}.{item_id}")

    async def list_items(self, collection: str) -> List[Dict[str, Any]]:
        """List all items in a collection.

        Args:
            collection: Collection name.

        Returns:
            List[Dict[str, Any]]: List of items in the collection.
        """
        try:
            item_ids = await self.list_data(collection)
            items = []

            for item_id in item_ids:
                item = await self.get_item(collection, item_id)
                if item:
                    items.append(item)

            return items

        except Exception as e:
            self.logger.error(f"Failed to list items in collection '{collection}': {e}")
            return []

    async def find_items(self, collection: str, filter_func: callable) -> List[Dict[str, Any]]:
        """Find items in a collection matching a filter function.

        Args:
            collection: Collection name.
            filter_func: Function that takes an item and returns True if it matches.

        Returns:
            List[Dict[str, Any]]: List of matching items.
        """
        items = await self.list_items(collection)
        return [item for item in items if filter_func(item)]

    async def count_items(self, collection: str) -> int:
        """Count items in a collection.

        Args:
            collection: Collection name.

        Returns:
            int: Number of items in the collection.
        """
        try:
            item_ids = await self.list_data(collection)
            return len(item_ids)
        except Exception:
            return 0

    def generate_id(self) -> str:
        """Generate a unique ID.

        Returns:
            str: Unique identifier string.
        """
        return str(uuid.uuid4())

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format.

        Returns:
            str: Current timestamp as ISO string.
        """
        return datetime.utcnow().isoformat()

    def clear_cache(self) -> None:
        """Clear the repository cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug("Repository cache cleared")

    def enable_cache(self, enabled: bool = True, ttl: int = 300) -> None:
        """Enable or disable caching.

        Args:
            enabled: Whether to enable caching.
            ttl: Cache TTL in seconds.
        """
        self._cache_enabled = enabled
        self._cache_ttl = ttl
        if not enabled:
            self.clear_cache()

    def _is_cache_valid(self, path: str) -> bool:
        """Check if cached data is still valid.

        Args:
            path: Data path to check.

        Returns:
            bool: True if cache is valid.
        """
        if path not in self._cache_timestamps:
            return False

        timestamp = self._cache_timestamps[path]
        age = (datetime.utcnow() - timestamp).total_seconds()
        return age < self._cache_ttl

    async def _load_from_database(self, path: str) -> Optional[Any]:
        """Load data from database.

        This is a placeholder implementation. In a real system, this would
        interface with the actual database (LiteDB, MongoDB, etc.).

        Args:
            path: Full database path.

        Returns:
            Optional[Any]: Data from database.
        """
        # TODO: Implement actual database integration
        # This would typically interface with app.db module
        try:
            # For now, simulate with file-based storage
            file_path = Path("data") / "plugins" / path.replace(".", "/")
            file_path = file_path.with_suffix(".json")
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"Database load error for {path}: {e}")
            return None

    async def _save_to_database(self, path: str, data: Any) -> bool:
        """Save data to database.

        Args:
            path: Full database path.
            data: Data to save.

        Returns:
            bool: True if successful.
        """
        # TODO: Implement actual database integration
        try:
            # For now, simulate with file-based storage
            file_path = Path("data") / "plugins" / path.replace(".", "/")
            file_path = file_path.with_suffix(".json")
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"Database save error for {path}: {e}")
            return False

    async def _delete_from_database(self, path: str) -> bool:
        """Delete data from database.

        Args:
            path: Full database path.

        Returns:
            bool: True if successful.
        """
        # TODO: Implement actual database integration
        try:
            file_path = Path("data") / "plugins" / path.replace(".", "/")
            file_path = file_path.with_suffix(".json")
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Database delete error for {path}: {e}")
            return False

    async def _list_from_database(self, path: str) -> List[str]:
        """List keys from database.

        Args:
            path: Full database path.

        Returns:
            List[str]: List of keys.
        """
        # TODO: Implement actual database integration
        try:
            dir_path = Path("data") / "plugins" / path.replace(".", "/")
            if dir_path.exists() and dir_path.is_dir():
                return [f.stem for f in dir_path.glob("*.json")]
            return []
        except Exception as e:
            self.logger.error(f"Database list error for {path}: {e}")
            return []

    async def backup_data(self) -> Dict[str, Any]:
        """Create a backup of all plugin data.

        Returns:
            Dict[str, Any]: Backup data.
        """
        try:
            backup = {
                "plugin_name": self.plugin_name,
                "category": self.category,
                "database_path": self.database_path,
                "backup_timestamp": self.get_timestamp(),
                "data": {}
            }

            # Get all data keys
            keys = await self.list_data()
            for key in keys:
                data = await self.get_data(key)
                if data is not None:
                    backup["data"][key] = data

            return backup

        except Exception as e:
            raise PluginDatabaseError(
                f"Failed to create backup: {str(e)}",
                plugin_name=self.plugin_name
            )

    async def restore_data(self, backup: Dict[str, Any]) -> bool:
        """Restore plugin data from backup.

        Args:
            backup: Backup data to restore.

        Returns:
            bool: True if successful.
        """
        try:
            if "data" not in backup:
                raise PluginDatabaseError(
                    "Invalid backup format: missing 'data' field",
                    plugin_name=self.plugin_name
                )

            # Restore each data item
            for key, data in backup["data"].items():
                await self.set_data(key, data)

            self.logger.info(f"Restored {len(backup['data'])} data items from backup")
            return True

        except Exception as e:
            raise PluginDatabaseError(
                f"Failed to restore from backup: {str(e)}",
                plugin_name=self.plugin_name
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics.

        Returns:
            Dict[str, Any]: Repository statistics.
        """
        return {
            "plugin_name": self.plugin_name,
            "category": self.category,
            "database_path": self.database_path,
            "cache_enabled": self._cache_enabled,
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl
        }

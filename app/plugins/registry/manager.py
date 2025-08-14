"""Plugin manager for the Firewallo Plugin Framework."""

import importlib
import json
import os
import asyncio
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import logging

from app.plugins.base import (
    BasePlugin,
    PluginError,
    PluginLoadError,
    PluginInitializationError,
    PluginNotFoundError,
    PluginAlreadyLoadedError,
    PluginNotLoadedError,
    PluginManifestError,
    PluginValidationError,
)


class PluginManager:
    """Manages plugin lifecycle and registration."""

    def __init__(self, plugin_dir: str = "app/plugins"):
        """Initialize the plugin manager.

        Args:
            plugin_dir: Base directory for plugins.
        """
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, dict] = {}
        self.enabled_plugins: set = set()
        self.logger = logging.getLogger("firewallo.plugins.manager")

        # Track plugin load order for dependency resolution
        self._load_order: List[str] = []

        # Cache for discovered plugins
        self._discovered_plugins: List[str] = []

    async def discover_plugins(self, plugin_dir: Optional[str] = None) -> List[str]:
        """Discover available plugins in the plugin directory.

        Args:
            plugin_dir: Optional override for plugin directory.

        Returns:
            List[str]: List of discovered plugin paths in format "category.plugin_name".
        """
        base_dir = plugin_dir or self.plugin_dir
        discovered = []

        try:
            if not os.path.exists(base_dir):
                self.logger.warning(f"Plugin directory {base_dir} does not exist")
                return discovered

            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)

                # Skip non-directories and private directories
                if not os.path.isdir(item_path) or item.startswith('_'):
                    continue

                # Skip base, registry, categories directories
                if item in ['base', 'registry', 'categories', '__pycache__']:
                    continue

                # This is a category directory
                category = item

                for plugin_name in os.listdir(item_path):
                    plugin_path = os.path.join(item_path, plugin_name)
                    manifest_path = os.path.join(plugin_path, "manifest.json")
                    plugin_file = os.path.join(plugin_path, "plugin.py")

                    if (os.path.isdir(plugin_path) and
                        os.path.exists(manifest_path) and
                        os.path.exists(plugin_file)):
                        plugin_identifier = f"{category}.{plugin_name}"
                        discovered.append(plugin_identifier)
                        self.logger.debug(f"Discovered plugin: {plugin_identifier}")

            self._discovered_plugins = discovered
            self.logger.info(f"Discovered {len(discovered)} plugins")
            return discovered

        except Exception as e:
            self.logger.error(f"Failed to discover plugins: {e}")
            return []

    async def load_plugin(self, plugin_path: str, enable: bool = True) -> bool:
        """Load a specific plugin.

        Args:
            plugin_path: Plugin identifier in format "category.plugin_name".
            enable: Whether to enable the plugin after loading.

        Returns:
            bool: True if loading was successful, False otherwise.

        Raises:
            PluginAlreadyLoadedError: If plugin is already loaded.
            PluginLoadError: If plugin loading fails.
        """
        if plugin_path in self.plugins:
            raise PluginAlreadyLoadedError(
                f"Plugin {plugin_path} is already loaded",
                plugin_name=plugin_path
            )

        try:
            self.logger.info(f"Loading plugin: {plugin_path}")

            # Load and validate manifest
            manifest = self._load_manifest(plugin_path)
            if not manifest:
                raise PluginManifestError(
                    f"Could not load manifest for plugin {plugin_path}",
                    plugin_name=plugin_path
                )

            # Validate manifest structure
            self._validate_manifest(manifest, plugin_path)

            # Import plugin module
            module_path = f"app.plugins.{plugin_path.replace('.', '.', 1)}.plugin"
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                raise PluginLoadError(
                    f"Could not import plugin module {module_path}: {e}",
                    plugin_name=plugin_path
                )

            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                raise PluginLoadError(
                    f"Could not find plugin class in {module_path}",
                    plugin_name=plugin_path
                )

            # Instantiate plugin
            plugin = plugin_class()
            plugin.set_manifest(manifest)

            # Validate plugin instance
            if not await self._validate_plugin(plugin, manifest):
                raise PluginValidationError(
                    f"Plugin validation failed for {plugin_path}",
                    plugin_name=plugin_path
                )

            # Initialize plugin
            try:
                if await plugin.initialize():
                    plugin.mark_initialized()
                    self.plugins[plugin_path] = plugin
                    self.plugin_configs[plugin_path] = manifest
                    self._load_order.append(plugin_path)

                    if enable:
                        await self.enable_plugin(plugin_path)

                    self.logger.info(f"Successfully loaded plugin: {plugin_path}")
                    return True
                else:
                    raise PluginInitializationError(
                        f"Plugin initialization returned False for {plugin_path}",
                        plugin_name=plugin_path
                    )

            except Exception as e:
                raise PluginInitializationError(
                    f"Plugin initialization failed for {plugin_path}: {e}",
                    plugin_name=plugin_path
                )

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
            if isinstance(e, PluginError):
                raise
            raise PluginLoadError(
                f"Unexpected error loading plugin {plugin_path}: {e}",
                plugin_name=plugin_path
            )

    async def unload_plugin(self, plugin_path: str) -> bool:
        """Unload a specific plugin.

        Args:
            plugin_path: Plugin identifier to unload.

        Returns:
            bool: True if unloading was successful, False otherwise.

        Raises:
            PluginNotLoadedError: If plugin is not loaded.
        """
        if plugin_path not in self.plugins:
            raise PluginNotLoadedError(
                f"Plugin {plugin_path} is not loaded",
                plugin_name=plugin_path
            )

        try:
            self.logger.info(f"Unloading plugin: {plugin_path}")

            plugin = self.plugins[plugin_path]

            # Disable first if enabled
            if plugin_path in self.enabled_plugins:
                await self.disable_plugin(plugin_path)

            # Shutdown plugin
            await plugin.shutdown()
            plugin.mark_shutdown()

            # Remove from tracking
            del self.plugins[plugin_path]
            if plugin_path in self.plugin_configs:
                del self.plugin_configs[plugin_path]
            if plugin_path in self._load_order:
                self._load_order.remove(plugin_path)

            self.logger.info(f"Successfully unloaded plugin: {plugin_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_path}: {e}")
            return False

    async def enable_plugin(self, plugin_path: str) -> bool:
        """Enable a loaded plugin.

        Args:
            plugin_path: Plugin identifier to enable.

        Returns:
            bool: True if enabling was successful, False otherwise.

        Raises:
            PluginNotLoadedError: If plugin is not loaded.
        """
        if plugin_path not in self.plugins:
            raise PluginNotLoadedError(
                f"Plugin {plugin_path} is not loaded",
                plugin_name=plugin_path
            )

        try:
            plugin = self.plugins[plugin_path]
            plugin.enabled = True
            self.enabled_plugins.add(plugin_path)

            self.logger.info(f"Enabled plugin: {plugin_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to enable plugin {plugin_path}: {e}")
            return False

    async def disable_plugin(self, plugin_path: str) -> bool:
        """Disable a loaded plugin.

        Args:
            plugin_path: Plugin identifier to disable.

        Returns:
            bool: True if disabling was successful, False otherwise.

        Raises:
            PluginNotLoadedError: If plugin is not loaded.
        """
        if plugin_path not in self.plugins:
            raise PluginNotLoadedError(
                f"Plugin {plugin_path} is not loaded",
                plugin_name=plugin_path
            )

        try:
            plugin = self.plugins[plugin_path]
            plugin.enabled = False
            self.enabled_plugins.discard(plugin_path)

            self.logger.info(f"Disabled plugin: {plugin_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to disable plugin {plugin_path}: {e}")
            return False

    def get_enabled_plugins(self, category: Optional[str] = None) -> List[BasePlugin]:
        """Get all enabled plugins, optionally filtered by category.

        Args:
            category: Optional category filter (vpn, firewall, monitoring, etc.).

        Returns:
            List[BasePlugin]: List of enabled plugins.
        """
        enabled = []
        for path, plugin in self.plugins.items():
            if plugin.enabled and path in self.enabled_plugins:
                if not category or plugin.category == category:
                    enabled.append(plugin)
        return enabled

    def get_plugin_routes(self) -> List:
        """Get API routes from all enabled plugins.

        Returns:
            List: List of FastAPI routers from enabled plugins.
        """
        routes = []
        for plugin in self.get_enabled_plugins():
            try:
                plugin_routes = plugin.get_api_routes()
                if plugin_routes:
                    routes.extend(plugin_routes)
            except Exception as e:
                self.logger.error(f"Failed to get routes from plugin {plugin.name}: {e}")
        return routes

    def get_plugin(self, plugin_path: str) -> Optional[BasePlugin]:
        """Get a loaded plugin by path.

        Args:
            plugin_path: Plugin identifier.

        Returns:
            Optional[BasePlugin]: Plugin instance if loaded, None otherwise.
        """
        return self.plugins.get(plugin_path)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins.

        Returns:
            Dict[str, BasePlugin]: Dictionary of all loaded plugins.
        """
        return self.plugins.copy()

    def get_plugin_info(self, plugin_path: Optional[str] = None) -> Dict[str, Any]:
        """Get plugin information.

        Args:
            plugin_path: Specific plugin to get info for. If None, returns info for all plugins.

        Returns:
            Dict[str, Any]: Plugin information.
        """
        if plugin_path:
            if plugin_path in self.plugins:
                return self.plugins[plugin_path].get_info()
            return {}

        return {
            path: plugin.get_info()
            for path, plugin in self.plugins.items()
        }

    def get_plugin_health(self, plugin_path: Optional[str] = None) -> Dict[str, Any]:
        """Get plugin health status.

        Args:
            plugin_path: Specific plugin to check. If None, returns health for all plugins.

        Returns:
            Dict[str, Any]: Plugin health information.
        """
        if plugin_path:
            if plugin_path in self.plugins:
                return self.plugins[plugin_path].get_health_status()
            return {}

        return {
            path: plugin.get_health_status()
            for path, plugin in self.plugins.items()
        }

    async def load_all_plugins(self, auto_enable: bool = True) -> Dict[str, bool]:
        """Load all discovered plugins.

        Args:
            auto_enable: Whether to automatically enable plugins after loading.

        Returns:
            Dict[str, bool]: Dictionary mapping plugin paths to load success status.
        """
        if not self._discovered_plugins:
            await self.discover_plugins()

        results = {}

        for plugin_path in self._discovered_plugins:
            try:
                success = await self.load_plugin(plugin_path, enable=auto_enable)
                results[plugin_path] = success
            except Exception as e:
                self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
                results[plugin_path] = False

        successful_loads = sum(1 for success in results.values() if success)
        self.logger.info(f"Loaded {successful_loads}/{len(results)} plugins")

        return results

    async def unload_all_plugins(self) -> Dict[str, bool]:
        """Unload all loaded plugins.

        Returns:
            Dict[str, bool]: Dictionary mapping plugin paths to unload success status.
        """
        results = {}

        # Unload in reverse order to handle dependencies
        for plugin_path in reversed(self._load_order):
            try:
                success = await self.unload_plugin(plugin_path)
                results[plugin_path] = success
            except Exception as e:
                self.logger.error(f"Failed to unload plugin {plugin_path}: {e}")
                results[plugin_path] = False

        return results

    async def reload_plugin(self, plugin_path: str) -> bool:
        """Reload a specific plugin.

        Args:
            plugin_path: Plugin identifier to reload.

        Returns:
            bool: True if reload was successful, False otherwise.
        """
        if plugin_path not in self.plugins:
            raise PluginNotLoadedError(
                f"Plugin {plugin_path} is not loaded",
                plugin_name=plugin_path
            )

        was_enabled = plugin_path in self.enabled_plugins

        # Unload and reload
        try:
            if await self.unload_plugin(plugin_path):
                return await self.load_plugin(plugin_path, enable=was_enabled)
            return False
        except Exception as e:
            self.logger.error(f"Failed to reload plugin {plugin_path}: {e}")
            return False

    def _load_manifest(self, plugin_path: str) -> Optional[Dict[str, Any]]:
        """Load plugin manifest file.

        Args:
            plugin_path: Plugin identifier.

        Returns:
            Optional[Dict[str, Any]]: Manifest data if successful, None otherwise.
        """
        try:
            # Convert plugin_path to file system path
            path_parts = plugin_path.split('.')
            if len(path_parts) != 2:
                return None

            category, plugin_name = path_parts
            manifest_file = os.path.join(self.plugin_dir, category, plugin_name, "manifest.json")

            if not os.path.exists(manifest_file):
                self.logger.error(f"Manifest file not found: {manifest_file}")
                return None

            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            return manifest

        except Exception as e:
            self.logger.error(f"Failed to load manifest for {plugin_path}: {e}")
            return None

    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """Find the plugin class in the module.

        Args:
            module: Python module to search.

        Returns:
            Optional[Type[BasePlugin]]: Plugin class if found, None otherwise.
        """
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue

            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, BasePlugin) and
                attr != BasePlugin):
                return attr
        return None

    async def _validate_plugin(self, plugin: BasePlugin, manifest: Dict[str, Any]) -> bool:
        """Validate plugin against its manifest.

        Args:
            plugin: Plugin instance to validate.
            manifest: Plugin manifest data.

        Returns:
            bool: True if validation passes, False otherwise.

        Raises:
            PluginValidationError: If validation fails.
        """
        try:
            # Validate required plugin attributes
            required_attrs = ['name', 'category', 'version']
            for attr in required_attrs:
                if not hasattr(plugin, attr) or not getattr(plugin, attr):
                    raise PluginValidationError(
                        f"Plugin missing required attribute: {attr}",
                        plugin_name=plugin.name
                    )

            # Validate manifest consistency
            if plugin.name != manifest.get('name'):
                raise PluginValidationError(
                    f"Plugin name mismatch: {plugin.name} vs {manifest.get('name')}",
                    plugin_name=plugin.name
                )

            if plugin.category != manifest.get('category'):
                raise PluginValidationError(
                    f"Plugin category mismatch: {plugin.category} vs {manifest.get('category')}",
                    plugin_name=plugin.name
                )

            # Validate required methods exist
            required_methods = ['initialize', 'shutdown', 'get_api_routes', 'get_database_schema']
            for method_name in required_methods:
                if not hasattr(plugin, method_name) or not callable(getattr(plugin, method_name)):
                    raise PluginValidationError(
                        f"Plugin missing required method: {method_name}",
                        plugin_name=plugin.name
                    )

            # Validate version format (basic semver check)
            version = plugin.version
            if not self._is_valid_version(version):
                raise PluginValidationError(
                    f"Invalid version format: {version}",
                    plugin_name=plugin.name
                )

            return True

        except Exception as e:
            if isinstance(e, PluginValidationError):
                raise
            raise PluginValidationError(
                f"Unexpected validation error: {e}",
                plugin_name=getattr(plugin, 'name', 'unknown')
            )

    def _validate_manifest(self, manifest: Dict[str, Any], plugin_path: str) -> None:
        """Validate manifest structure and required fields.

        Args:
            manifest: Manifest data to validate.
            plugin_path: Plugin identifier for error reporting.

        Raises:
            PluginManifestError: If manifest validation fails.
        """
        required_fields = ['name', 'category', 'version', 'description']

        for field in required_fields:
            if field not in manifest:
                raise PluginManifestError(
                    f"Manifest missing required field: {field}",
                    plugin_name=plugin_path
                )

        # Validate category is supported
        supported_categories = ['vpn', 'firewall', 'monitoring', 'network', 'security']
        if manifest['category'] not in supported_categories:
            raise PluginManifestError(
                f"Unsupported plugin category: {manifest['category']}",
                plugin_name=plugin_path
            )

    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid semver format.

        Args:
            version: Version string to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False

            for part in parts:
                int(part)  # Should be parseable as int

            return True
        except (ValueError, AttributeError):
            return False

    def get_load_order(self) -> List[str]:
        """Get the order in which plugins were loaded.

        Returns:
            List[str]: Plugin paths in load order.
        """
        return self._load_order.copy()

    def get_discovered_plugins(self) -> List[str]:
        """Get list of discovered plugins.

        Returns:
            List[str]: List of discovered plugin paths.
        """
        return self._discovered_plugins.copy()

    def is_plugin_loaded(self, plugin_path: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_path: Plugin identifier to check.

        Returns:
            bool: True if plugin is loaded, False otherwise.
        """
        return plugin_path in self.plugins

    def is_plugin_enabled(self, plugin_path: str) -> bool:
        """Check if a plugin is enabled.

        Args:
            plugin_path: Plugin identifier to check.

        Returns:
            bool: True if plugin is enabled, False otherwise.
        """
        return plugin_path in self.enabled_plugins

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics.

        Returns:
            Dict[str, Any]: Manager statistics including counts and status.
        """
        total_plugins = len(self.plugins)
        enabled_plugins = len(self.enabled_plugins)
        disabled_plugins = total_plugins - enabled_plugins

        categories = {}
        for plugin in self.plugins.values():
            category = plugin.category
            if category not in categories:
                categories[category] = {'total': 0, 'enabled': 0}
            categories[category]['total'] += 1
            if plugin.enabled:
                categories[category]['enabled'] += 1

        return {
            "total_discovered": len(self._discovered_plugins),
            "total_loaded": total_plugins,
            "total_enabled": enabled_plugins,
            "total_disabled": disabled_plugins,
            "categories": categories,
            "load_order": self._load_order.copy()
        }


# Global plugin manager instance
plugin_manager = PluginManager()

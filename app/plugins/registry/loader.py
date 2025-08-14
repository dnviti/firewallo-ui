"""Plugin loader utility for the Firewallo Plugin Framework."""

import importlib
import importlib.util
import sys
from typing import Dict, List, Optional, Type, Any, Set
from pathlib import Path
import logging
import json
import os

from app.plugins.base import (
    BasePlugin,
    PluginError,
    PluginLoadError,
    PluginDependencyError,
    PluginManifestError,
    PluginVersionError,
)


class PluginLoader:
    """Handles dynamic loading and importing of plugins."""

    def __init__(self, plugin_dir: str = "app/plugins"):
        """Initialize the plugin loader.

        Args:
            plugin_dir: Base directory for plugins.
        """
        self.plugin_dir = plugin_dir
        self.logger = logging.getLogger("firewallo.plugins.loader")

        # Cache for loaded modules to support hot reloading
        self._module_cache: Dict[str, Any] = {}

        # Track module dependencies
        self._dependency_graph: Dict[str, Set[str]] = {}

        # Track load attempts to prevent infinite recursion
        self._loading: Set[str] = set()

    def load_plugin_module(self, plugin_path: str, reload: bool = False) -> Any:
        """Load a plugin module dynamically.

        Args:
            plugin_path: Plugin identifier in format "category.plugin_name".
            reload: Whether to force reload the module.

        Returns:
            Any: The loaded Python module.

        Raises:
            PluginLoadError: If module loading fails.
        """
        if plugin_path in self._loading:
            raise PluginLoadError(
                f"Circular dependency detected for plugin {plugin_path}",
                plugin_name=plugin_path
            )

        try:
            self._loading.add(plugin_path)

            # Check cache first
            if not reload and plugin_path in self._module_cache:
                self.logger.debug(f"Using cached module for {plugin_path}")
                return self._module_cache[plugin_path]

            # Convert plugin path to module path
            module_path = f"app.plugins.{plugin_path.replace('.', '.', 1)}.plugin"

            # Load the module
            if reload and module_path in sys.modules:
                # Force reload
                module = importlib.reload(sys.modules[module_path])
                self.logger.debug(f"Reloaded module {module_path}")
            else:
                # Fresh import
                module = importlib.import_module(module_path)
                self.logger.debug(f"Imported module {module_path}")

            # Cache the module
            self._module_cache[plugin_path] = module

            return module

        except ImportError as e:
            raise PluginLoadError(
                f"Failed to import plugin module {plugin_path}: {e}",
                plugin_name=plugin_path
            )
        except Exception as e:
            raise PluginLoadError(
                f"Unexpected error loading plugin module {plugin_path}: {e}",
                plugin_name=plugin_path
            )
        finally:
            self._loading.discard(plugin_path)

    def find_plugin_class(self, module: Any, plugin_path: str) -> Type[BasePlugin]:
        """Find the main plugin class in a module.

        Args:
            module: Python module to search.
            plugin_path: Plugin identifier for error reporting.

        Returns:
            Type[BasePlugin]: The plugin class.

        Raises:
            PluginLoadError: If no valid plugin class is found.
        """
        plugin_classes = []

        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue

            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, BasePlugin) and
                attr != BasePlugin):
                plugin_classes.append((attr_name, attr))

        if not plugin_classes:
            raise PluginLoadError(
                f"No plugin class found in module for {plugin_path}",
                plugin_name=plugin_path
            )

        if len(plugin_classes) == 1:
            return plugin_classes[0][1]

        # Multiple classes found - try to find the main one
        # Look for class names that match patterns
        preferred_patterns = [
            plugin_path.split('.')[-1].title() + "Plugin",
            plugin_path.split('.')[-1].title(),
            "Plugin",
            "Main",
        ]

        for pattern in preferred_patterns:
            for class_name, class_obj in plugin_classes:
                if class_name == pattern:
                    return class_obj

        # If no preferred pattern matches, use the first one but log a warning
        self.logger.warning(
            f"Multiple plugin classes found for {plugin_path}, using {plugin_classes[0][0]}"
        )
        return plugin_classes[0][1]

    def load_plugin_manifest(self, plugin_path: str) -> Dict[str, Any]:
        """Load and validate plugin manifest.

        Args:
            plugin_path: Plugin identifier.

        Returns:
            Dict[str, Any]: Validated manifest data.

        Raises:
            PluginManifestError: If manifest loading/validation fails.
        """
        try:
            # Convert plugin path to file system path
            path_parts = plugin_path.split('.')
            if len(path_parts) != 2:
                raise PluginManifestError(
                    f"Invalid plugin path format: {plugin_path}",
                    plugin_name=plugin_path
                )

            category, plugin_name = path_parts
            manifest_file = Path(self.plugin_dir) / category / plugin_name / "manifest.json"

            if not manifest_file.exists():
                raise PluginManifestError(
                    f"Manifest file not found: {manifest_file}",
                    plugin_name=plugin_path
                )

            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # Validate manifest structure
            self._validate_manifest_structure(manifest, plugin_path)

            return manifest

        except json.JSONDecodeError as e:
            raise PluginManifestError(
                f"Invalid JSON in manifest for {plugin_path}: {e}",
                plugin_name=plugin_path
            )
        except Exception as e:
            if isinstance(e, PluginManifestError):
                raise
            raise PluginManifestError(
                f"Failed to load manifest for {plugin_path}: {e}",
                plugin_name=plugin_path
            )

    def validate_dependencies(self, manifest: Dict[str, Any], plugin_path: str) -> List[str]:
        """Validate plugin dependencies.

        Args:
            manifest: Plugin manifest data.
            plugin_path: Plugin identifier.

        Returns:
            List[str]: List of missing dependencies.

        Raises:
            PluginDependencyError: If critical dependencies are missing.
        """
        missing_deps = []
        dependencies = manifest.get('dependencies', {})

        # Check Python version
        python_req = dependencies.get('python')
        if python_req:
            if not self._check_python_version(python_req):
                missing_deps.append(f"Python {python_req}")

        # Check Python packages
        packages = dependencies.get('packages', [])
        for package in packages:
            if not self._check_package_available(package):
                missing_deps.append(f"Python package: {package}")

        # Check system dependencies
        system_deps = dependencies.get('system', [])
        for dep in system_deps:
            if not self._check_system_dependency(dep):
                missing_deps.append(f"System dependency: {dep}")

        # Check Firewallo version
        min_version = manifest.get('min_firewallo_version')
        max_version = manifest.get('max_firewallo_version')

        if min_version or max_version:
            current_version = self._get_firewallo_version()
            if min_version and not self._version_compare(current_version, min_version, '>='):
                missing_deps.append(f"Firewallo >= {min_version} (current: {current_version})")
            if max_version and not self._version_compare(current_version, max_version, '<='):
                missing_deps.append(f"Firewallo <= {max_version} (current: {current_version})")

        return missing_deps

    def resolve_load_order(self, plugin_paths: List[str]) -> List[str]:
        """Resolve plugin load order based on dependencies.

        Args:
            plugin_paths: List of plugin identifiers to order.

        Returns:
            List[str]: Plugin paths ordered for loading.

        Raises:
            PluginDependencyError: If circular dependencies are detected.
        """
        # Build dependency graph
        graph = {}
        manifests = {}

        for plugin_path in plugin_paths:
            try:
                manifest = self.load_plugin_manifest(plugin_path)
                manifests[plugin_path] = manifest

                # Extract plugin dependencies (other plugins)
                plugin_deps = manifest.get('plugin_dependencies', [])
                graph[plugin_path] = set(plugin_deps)

            except Exception as e:
                self.logger.warning(f"Failed to load manifest for {plugin_path}: {e}")
                graph[plugin_path] = set()

        # Topological sort
        ordered = []
        visited = set()
        visiting = set()

        def visit(plugin: str):
            if plugin in visiting:
                raise PluginDependencyError(
                    f"Circular dependency detected involving {plugin}",
                    plugin_name=plugin
                )

            if plugin in visited:
                return

            visiting.add(plugin)

            for dep in graph.get(plugin, set()):
                if dep in plugin_paths:  # Only consider deps that are being loaded
                    visit(dep)

            visiting.remove(plugin)
            visited.add(plugin)
            ordered.append(plugin)

        for plugin_path in plugin_paths:
            visit(plugin_path)

        return ordered

    def _validate_manifest_structure(self, manifest: Dict[str, Any], plugin_path: str) -> None:
        """Validate manifest has required structure.

        Args:
            manifest: Manifest data to validate.
            plugin_path: Plugin identifier for error reporting.

        Raises:
            PluginManifestError: If validation fails.
        """
        required_fields = ['name', 'category', 'version', 'description']

        for field in required_fields:
            if field not in manifest:
                raise PluginManifestError(
                    f"Manifest missing required field: {field}",
                    plugin_name=plugin_path
                )

        # Validate version format
        version = manifest['version']
        if not self._is_valid_version(version):
            raise PluginManifestError(
                f"Invalid version format: {version}",
                plugin_name=plugin_path
            )

        # Validate category
        valid_categories = ['vpn', 'firewall', 'monitoring', 'network', 'security']
        if manifest['category'] not in valid_categories:
            raise PluginManifestError(
                f"Invalid category: {manifest['category']}. Must be one of {valid_categories}",
                plugin_name=plugin_path
            )

    def _check_python_version(self, requirement: str) -> bool:
        """Check if current Python version meets requirement.

        Args:
            requirement: Version requirement string (e.g., ">=3.11").

        Returns:
            bool: True if requirement is met.
        """
        try:
            import sys
            current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            if requirement.startswith('>='):
                required = requirement[2:]
                return self._version_compare(current, required, '>=')
            elif requirement.startswith('<='):
                required = requirement[2:]
                return self._version_compare(current, required, '<=')
            elif requirement.startswith('>'):
                required = requirement[1:]
                return self._version_compare(current, required, '>')
            elif requirement.startswith('<'):
                required = requirement[1:]
                return self._version_compare(current, required, '<')
            elif requirement.startswith('=='):
                required = requirement[2:]
                return self._version_compare(current, required, '==')
            else:
                # Assume exact match
                return self._version_compare(current, requirement, '==')
        except Exception:
            return False

    def _check_package_available(self, package: str) -> bool:
        """Check if a Python package is available.

        Args:
            package: Package specification (e.g., "requests>=2.0.0").

        Returns:
            bool: True if package is available.
        """
        try:
            # Parse package name and version
            if '>=' in package:
                name, version = package.split('>=')
                name = name.strip()
                version = version.strip()
            elif '==' in package:
                name, version = package.split('==')
                name = name.strip()
                version = version.strip()
            else:
                name = package.strip()
                version = None

            # Try to import the package
            importlib.import_module(name)

            # TODO: Check version if specified
            # This would require parsing __version__ attributes

            return True
        except ImportError:
            return False

    def _check_system_dependency(self, dependency: str) -> bool:
        """Check if a system dependency is available.

        Args:
            dependency: System dependency name.

        Returns:
            bool: True if dependency is available.
        """
        try:
            import shutil
            return shutil.which(dependency) is not None
        except Exception:
            return False

    def _get_firewallo_version(self) -> str:
        """Get current Firewallo version.

        Returns:
            str: Current version string.
        """
        try:
            # Try to get version from package or config
            # For now, return a default version
            return "1.0.0"
        except Exception:
            return "0.0.0"

    def _version_compare(self, version1: str, version2: str, operator: str) -> bool:
        """Compare two version strings.

        Args:
            version1: First version string.
            version2: Second version string.
            operator: Comparison operator (>=, <=, >, <, ==).

        Returns:
            bool: True if comparison is true.
        """
        try:
            def parse_version(v):
                return tuple(map(int, v.split('.')))

            v1 = parse_version(version1)
            v2 = parse_version(version2)

            if operator == '>=':
                return v1 >= v2
            elif operator == '<=':
                return v1 <= v2
            elif operator == '>':
                return v1 > v2
            elif operator == '<':
                return v1 < v2
            elif operator == '==':
                return v1 == v2
            else:
                return False
        except Exception:
            return False

    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid semver format.

        Args:
            version: Version string to validate.

        Returns:
            bool: True if valid.
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

    def clear_cache(self, plugin_path: Optional[str] = None) -> None:
        """Clear module cache.

        Args:
            plugin_path: Specific plugin to clear. If None, clears all.
        """
        if plugin_path:
            self._module_cache.pop(plugin_path, None)
            self.logger.debug(f"Cleared cache for {plugin_path}")
        else:
            self._module_cache.clear()
            self.logger.debug("Cleared all module cache")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the module cache.

        Returns:
            Dict[str, Any]: Cache information.
        """
        return {
            "cached_modules": len(self._module_cache),
            "modules": list(self._module_cache.keys()),
            "dependency_graph": {
                k: list(v) for k, v in self._dependency_graph.items()
            }
        }

"""Plugin validator for the Firewallo Plugin Framework."""

import json
import re
import ast
import importlib
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import logging

from app.plugins.base import (
    PluginError,
    PluginValidationError,
    PluginManifestError,
    PluginPermissionError,
    PluginDependencyError,
    PluginSecurityError,
    PluginVersionError,
)


class PluginValidator:
    """Validates plugins for security, compliance, and correctness."""

    def __init__(self):
        """Initialize the plugin validator."""
        self.logger = logging.getLogger("firewallo.plugins.validator")

        # Define security restrictions
        self._forbidden_imports = {
            'os.system', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
            'eval', 'exec', '__import__', 'compile', 'globals', 'locals',
            'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr'
        }

        # Define allowed system packages
        self._safe_packages = {
            'requests', 'urllib3', 'httpx', 'aiohttp',
            'cryptography', 'pynacl', 'bcrypt', 'passlib',
            'pydantic', 'fastapi', 'starlette',
            'sqlalchemy', 'asyncpg', 'psycopg2',
            'redis', 'pymongo',
            'pytest', 'unittest',
            'logging', 'json', 're', 'datetime', 'time',
            'typing', 'dataclasses', 'enum', 'collections',
            'pathlib', 'uuid', 'hashlib', 'base64',
            'asyncio', 'concurrent.futures',
            'ipaddress', 'socket', 'ssl',
        }

        # Define required permissions for operations
        self._permission_requirements = {
            'network.create': ['socket', 'requests', 'aiohttp', 'httpx'],
            'network.modify': ['iptables', 'netfilter', 'routing'],
            'system.execute': ['subprocess', 'os.system'],
            'file.read': ['open', 'pathlib'],
            'file.write': ['open', 'pathlib'],
            'database.read': ['sqlalchemy', 'asyncpg', 'pymongo'],
            'database.write': ['sqlalchemy', 'asyncpg', 'pymongo'],
        }

    def validate_plugin_complete(self, plugin_path: str, plugin_dir: str = "app/plugins") -> Dict[str, Any]:
        """Perform complete plugin validation.

        Args:
            plugin_path: Plugin identifier in format "category.plugin_name".
            plugin_dir: Base plugin directory.

        Returns:
            Dict[str, Any]: Validation results with details.

        Raises:
            PluginValidationError: If validation fails.
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'manifest': None,
            'permissions': [],
            'dependencies': [],
            'security_issues': []
        }

        try:
            # Validate manifest
            manifest_result = self.validate_manifest(plugin_path, plugin_dir)
            results['manifest'] = manifest_result
            if not manifest_result['valid']:
                results['valid'] = False
                results['errors'].extend(manifest_result['errors'])

            if results['manifest'] and results['manifest'].get('data'):
                manifest = results['manifest']['data']

                # Validate permissions
                perm_result = self.validate_permissions(manifest, plugin_path)
                results['permissions'] = perm_result
                if not perm_result['valid']:
                    results['warnings'].extend(perm_result['warnings'])

                # Validate dependencies
                dep_result = self.validate_dependencies(manifest, plugin_path)
                results['dependencies'] = dep_result
                if not dep_result['valid']:
                    results['valid'] = False
                    results['errors'].extend(dep_result['errors'])

                # Security validation
                sec_result = self.validate_security(plugin_path, plugin_dir, manifest)
                results['security_issues'] = sec_result
                if not sec_result['valid']:
                    results['valid'] = False
                    results['errors'].extend(sec_result['errors'])
                    results['warnings'].extend(sec_result['warnings'])

        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation failed: {str(e)}")
            self.logger.error(f"Plugin validation failed for {plugin_path}: {e}")

        return results

    def validate_manifest(self, plugin_path: str, plugin_dir: str = "app/plugins") -> Dict[str, Any]:
        """Validate plugin manifest file.

        Args:
            plugin_path: Plugin identifier.
            plugin_dir: Base plugin directory.

        Returns:
            Dict[str, Any]: Manifest validation results.
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'data': None
        }

        try:
            # Load manifest file
            path_parts = plugin_path.split('.')
            if len(path_parts) != 2:
                result['valid'] = False
                result['errors'].append("Invalid plugin path format")
                return result

            category, plugin_name = path_parts
            manifest_file = Path(plugin_dir) / category / plugin_name / "manifest.json"

            if not manifest_file.exists():
                result['valid'] = False
                result['errors'].append(f"Manifest file not found: {manifest_file}")
                return result

            # Parse JSON
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                result['data'] = manifest
            except json.JSONDecodeError as e:
                result['valid'] = False
                result['errors'].append(f"Invalid JSON in manifest: {e}")
                return result

            # Validate required fields
            required_fields = {
                'name': str,
                'category': str,
                'version': str,
                'description': str,
                'author': str,
            }

            for field, expected_type in required_fields.items():
                if field not in manifest:
                    result['valid'] = False
                    result['errors'].append(f"Missing required field: {field}")
                elif not isinstance(manifest[field], expected_type):
                    result['valid'] = False
                    result['errors'].append(f"Field {field} must be of type {expected_type.__name__}")

            if not result['valid']:
                return result

            # Validate field values
            if manifest['name'] != plugin_name:
                result['valid'] = False
                result['errors'].append(f"Manifest name '{manifest['name']}' doesn't match plugin name '{plugin_name}'")

            if manifest['category'] != category:
                result['valid'] = False
                result['errors'].append(f"Manifest category '{manifest['category']}' doesn't match directory '{category}'")

            # Validate version format
            if not self._is_valid_version(manifest['version']):
                result['valid'] = False
                result['errors'].append(f"Invalid version format: {manifest['version']}")

            # Validate category
            valid_categories = ['vpn', 'firewall', 'monitoring', 'network', 'security']
            if manifest['category'] not in valid_categories:
                result['valid'] = False
                result['errors'].append(f"Invalid category: {manifest['category']}")

            # Validate optional fields
            if 'dependencies' in manifest:
                if not isinstance(manifest['dependencies'], dict):
                    result['warnings'].append("Dependencies should be a dictionary")

            if 'permissions' in manifest:
                if not isinstance(manifest['permissions'], list):
                    result['warnings'].append("Permissions should be a list")

            if 'configuration' in manifest:
                if not isinstance(manifest['configuration'], dict):
                    result['warnings'].append("Configuration should be a dictionary")

            # Check for deprecated fields
            deprecated_fields = ['deprecated_field_example']
            for field in deprecated_fields:
                if field in manifest:
                    result['warnings'].append(f"Field '{field}' is deprecated")

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Manifest validation failed: {str(e)}")

        return result

    def validate_permissions(self, manifest: Dict[str, Any], plugin_path: str) -> Dict[str, Any]:
        """Validate plugin permissions.

        Args:
            manifest: Plugin manifest data.
            plugin_path: Plugin identifier.

        Returns:
            Dict[str, Any]: Permission validation results.
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'requested_permissions': [],
            'dangerous_permissions': []
        }

        permissions = manifest.get('permissions', [])
        result['requested_permissions'] = permissions

        # Define permission categories
        dangerous_permissions = [
            'system.execute',
            'system.admin',
            'file.write',
            'network.raw',
            'database.admin'
        ]

        high_risk_permissions = [
            'network.modify',
            'system.service',
            'file.delete',
            'database.write'
        ]

        for permission in permissions:
            if not self._is_valid_permission(permission):
                result['warnings'].append(f"Unknown permission: {permission}")

            if permission in dangerous_permissions:
                result['dangerous_permissions'].append(permission)
                result['warnings'].append(f"Dangerous permission requested: {permission}")

            if permission in high_risk_permissions:
                result['warnings'].append(f"High-risk permission requested: {permission}")

        # Check if permissions match plugin category
        category = manifest.get('category', '')
        expected_permissions = self._get_expected_permissions(category)

        unnecessary_permissions = set(permissions) - set(expected_permissions)
        if unnecessary_permissions:
            result['warnings'].append(f"Unexpected permissions for {category} plugin: {list(unnecessary_permissions)}")

        return result

    def validate_dependencies(self, manifest: Dict[str, Any], plugin_path: str) -> Dict[str, Any]:
        """Validate plugin dependencies.

        Args:
            manifest: Plugin manifest data.
            plugin_path: Plugin identifier.

        Returns:
            Dict[str, Any]: Dependency validation results.
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_dependencies': [],
            'unsafe_packages': []
        }

        dependencies = manifest.get('dependencies', {})

        # Validate Python version
        python_req = dependencies.get('python')
        if python_req:
            if not self._is_valid_version_requirement(python_req):
                result['errors'].append(f"Invalid Python version requirement: {python_req}")
                result['valid'] = False

        # Validate Python packages
        packages = dependencies.get('packages', [])
        for package in packages:
            package_name = self._extract_package_name(package)

            if not self._is_safe_package(package_name):
                result['unsafe_packages'].append(package)
                result['warnings'].append(f"Potentially unsafe package: {package}")

            # Check if package is available (optional check)
            if not self._check_package_available(package_name):
                result['missing_dependencies'].append(package)

        # Validate system dependencies
        system_deps = dependencies.get('system', [])
        for dep in system_deps:
            if not self._is_safe_system_dependency(dep):
                result['warnings'].append(f"Potentially unsafe system dependency: {dep}")

        # Check version constraints
        min_version = manifest.get('min_firewallo_version')
        max_version = manifest.get('max_firewallo_version')

        if min_version and not self._is_valid_version(min_version):
            result['errors'].append(f"Invalid min_firewallo_version: {min_version}")
            result['valid'] = False

        if max_version and not self._is_valid_version(max_version):
            result['errors'].append(f"Invalid max_firewallo_version: {max_version}")
            result['valid'] = False

        return result

    def validate_security(self, plugin_path: str, plugin_dir: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Perform security validation on plugin code.

        Args:
            plugin_path: Plugin identifier.
            plugin_dir: Base plugin directory.
            manifest: Plugin manifest data.

        Returns:
            Dict[str, Any]: Security validation results.
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'security_issues': [],
            'code_analysis': {}
        }

        try:
            # Analyze main plugin file
            path_parts = plugin_path.split('.')
            category, plugin_name = path_parts
            plugin_file = Path(plugin_dir) / category / plugin_name / "plugin.py"

            if plugin_file.exists():
                code_result = self._analyze_code_security(plugin_file, plugin_path)
                result['code_analysis'] = code_result

                if not code_result['safe']:
                    result['valid'] = False
                    result['security_issues'].extend(code_result['issues'])
                    result['errors'].extend(code_result['critical_issues'])
                    result['warnings'].extend(code_result['warnings'])

            # Check file permissions
            file_perms = self._check_file_permissions(plugin_dir, plugin_path)
            if file_perms['issues']:
                result['warnings'].extend(file_perms['issues'])

            # Validate against manifest permissions
            perm_issues = self._validate_code_permissions(result['code_analysis'], manifest)
            if perm_issues:
                result['warnings'].extend(perm_issues)

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Security validation failed: {str(e)}")

        return result

    def _analyze_code_security(self, file_path: Path, plugin_path: str) -> Dict[str, Any]:
        """Analyze Python code for security issues.

        Args:
            file_path: Path to Python file.
            plugin_path: Plugin identifier.

        Returns:
            Dict[str, Any]: Code analysis results.
        """
        result = {
            'safe': True,
            'issues': [],
            'critical_issues': [],
            'warnings': [],
            'imports': [],
            'function_calls': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Parse AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                result['safe'] = False
                result['critical_issues'].append(f"Syntax error in {file_path}: {e}")
                return result

            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_import_security(alias.name, result)

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        full_name = f"{module}.{alias.name}" if module else alias.name
                        self._check_import_security(full_name, result)

                elif isinstance(node, ast.Call):
                    self._check_function_call_security(node, result)

                elif isinstance(node, ast.Exec):
                    result['safe'] = False
                    result['critical_issues'].append("Use of 'exec' statement detected")

                elif isinstance(node, ast.Eval):
                    result['safe'] = False
                    result['critical_issues'].append("Use of 'eval' function detected")

        except Exception as e:
            result['safe'] = False
            result['critical_issues'].append(f"Code analysis failed: {str(e)}")

        return result

    def _check_import_security(self, import_name: str, result: Dict[str, Any]) -> None:
        """Check if an import is secure.

        Args:
            import_name: Name of the imported module/function.
            result: Result dictionary to update.
        """
        result['imports'].append(import_name)

        if import_name in self._forbidden_imports:
            result['safe'] = False
            result['critical_issues'].append(f"Forbidden import: {import_name}")

        # Check for potentially dangerous modules
        dangerous_modules = ['os', 'subprocess', 'sys', '__builtin__', 'builtins']
        for dangerous in dangerous_modules:
            if import_name.startswith(dangerous + '.'):
                result['warnings'].append(f"Potentially dangerous import: {import_name}")

    def _check_function_call_security(self, node: ast.Call, result: Dict[str, Any]) -> None:
        """Check if a function call is secure.

        Args:
            node: AST Call node.
            result: Result dictionary to update.
        """
        func_name = self._get_function_name(node.func)
        if func_name:
            result['function_calls'].append(func_name)

            # Check for dangerous functions
            dangerous_functions = ['exec', 'eval', 'compile', '__import__', 'open']
            if func_name in dangerous_functions:
                result['warnings'].append(f"Potentially dangerous function call: {func_name}")

    def _get_function_name(self, node: ast.AST) -> Optional[str]:
        """Extract function name from AST node.

        Args:
            node: AST node representing a function.

        Returns:
            Optional[str]: Function name if extractable.
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        return None

    def _check_file_permissions(self, plugin_dir: str, plugin_path: str) -> Dict[str, Any]:
        """Check file system permissions.

        Args:
            plugin_dir: Base plugin directory.
            plugin_path: Plugin identifier.

        Returns:
            Dict[str, Any]: File permission check results.
        """
        result = {'issues': []}

        try:
            path_parts = plugin_path.split('.')
            category, plugin_name = path_parts
            plugin_folder = Path(plugin_dir) / category / plugin_name

            if plugin_folder.exists():
                # Check for executable files
                for file_path in plugin_folder.rglob('*'):
                    if file_path.is_file() and file_path.stat().st_mode & 0o111:
                        result['issues'].append(f"Executable file found: {file_path}")

        except Exception as e:
            result['issues'].append(f"File permission check failed: {str(e)}")

        return result

    def _validate_code_permissions(self, code_analysis: Dict[str, Any], manifest: Dict[str, Any]) -> List[str]:
        """Validate that code operations match declared permissions.

        Args:
            code_analysis: Results from code analysis.
            manifest: Plugin manifest data.

        Returns:
            List[str]: List of permission issues.
        """
        issues = []
        declared_permissions = set(manifest.get('permissions', []))

        # Check if code uses operations requiring undeclared permissions
        imports = code_analysis.get('imports', [])

        for import_name in imports:
            required_perms = self._get_required_permissions_for_import(import_name)
            missing_perms = required_perms - declared_permissions

            if missing_perms:
                issues.append(f"Import '{import_name}' requires undeclared permissions: {list(missing_perms)}")

        return issues

    def _get_required_permissions_for_import(self, import_name: str) -> Set[str]:
        """Get required permissions for an import.

        Args:
            import_name: Name of the imported module.

        Returns:
            Set[str]: Set of required permissions.
        """
        permissions = set()

        for perm, modules in self._permission_requirements.items():
            if any(import_name.startswith(module) for module in modules):
                permissions.add(perm)

        return permissions

    def _is_valid_permission(self, permission: str) -> bool:
        """Check if permission string is valid.

        Args:
            permission: Permission string to validate.

        Returns:
            bool: True if valid.
        """
        # Permission format: category.action
        pattern = r'^[a-z]+\.[a-z]+$'
        return bool(re.match(pattern, permission))

    def _get_expected_permissions(self, category: str) -> List[str]:
        """Get expected permissions for a plugin category.

        Args:
            category: Plugin category.

        Returns:
            List[str]: List of expected permissions.
        """
        category_permissions = {
            'vpn': ['network.create', 'network.modify', 'system.execute'],
            'firewall': ['network.modify', 'system.execute'],
            'monitoring': ['network.read', 'system.read'],
            'network': ['network.create', 'network.read'],
            'security': ['system.read', 'network.read', 'file.read']
        }

        return category_permissions.get(category, [])

    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid semver format.

        Args:
            version: Version string to validate.

        Returns:
            bool: True if valid.
        """
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))

    def _is_valid_version_requirement(self, requirement: str) -> bool:
        """Check if version requirement is valid.

        Args:
            requirement: Version requirement string.

        Returns:
            bool: True if valid.
        """
        pattern = r'^(>=|<=|>|<|==)?\d+\.\d+(\.\d+)?$'
        return bool(re.match(pattern, requirement))

    def _extract_package_name(self, package_spec: str) -> str:
        """Extract package name from specification.

        Args:
            package_spec: Package specification (e.g., "requests>=2.0.0").

        Returns:
            str: Package name.
        """
        for operator in ['>=', '<=', '==', '>', '<']:
            if operator in package_spec:
                return package_spec.split(operator)[0].strip()
        return package_spec.strip()

    def _is_safe_package(self, package_name: str) -> bool:
        """Check if a package is considered safe.

        Args:
            package_name: Name of the package.

        Returns:
            bool: True if safe.
        """
        return package_name in self._safe_packages

    def _check_package_available(self, package_name: str) -> bool:
        """Check if a package is available.

        Args:
            package_name: Name of the package.

        Returns:
            bool: True if available.
        """
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

    def _is_safe_system_dependency(self, dependency: str) -> bool:
        """Check if a system dependency is safe.

        Args:
            dependency: System dependency name.

        Returns:
            bool: True if safe.
        """
        # List of safe system dependencies
        safe_deps = [
            'openssl', 'curl', 'wget', 'git',
            'python3', 'pip', 'nodejs', 'npm',
            'docker', 'systemctl'
        ]

        return dependency in safe_deps

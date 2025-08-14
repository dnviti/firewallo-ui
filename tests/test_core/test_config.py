#!/usr/bin/env python3
"""
Core configuration tests for Firewallo UI.

Tests the core configuration system including:
- Configuration loading and validation
- Environment variable handling
- Default value management
- Configuration file parsing
- Settings validation
"""

import pytest
import os
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Test markers
pytestmark = [pytest.mark.core, pytest.mark.unit, pytest.mark.asyncio]


class TestConfigurationLoading:
    """Test configuration loading functionality."""

    def test_load_default_config(self, mock_env_vars):
        """Test loading default configuration."""
        from app.core.config import Config, load_config

        config = load_config()

        assert isinstance(config, Config)
        assert config.debug is True  # From test environment
        assert config.database_url is not None
        assert config.secret_key is not None

    def test_load_config_from_file(self, temp_dir):
        """Test loading configuration from file."""
        from app.core.config import load_config_from_file

        # Create test config file
        config_data = {
            "database": {
                "url": "postgresql://test:test@localhost/testdb",
                "pool_size": 10
            },
            "auth": {
                "secret_key": "test-secret-key",
                "algorithm": "HS256",
                "token_expire_minutes": 60
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8080,
                "reload": False
            }
        }

        config_file = temp_dir / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = load_config_from_file(str(config_file))

        assert config["database"]["url"] == "postgresql://test:test@localhost/testdb"
        assert config["database"]["pool_size"] == 10
        assert config["auth"]["secret_key"] == "test-secret-key"
        assert config["api"]["port"] == 8080

    def test_load_config_yaml_format(self, temp_dir):
        """Test loading configuration from YAML file."""
        from app.core.config import load_config_from_file

        config_data = {
            "database": {
                "url": "sqlite:///test.db",
                "pool_size": 5
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            }
        }

        config_file = temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = load_config_from_file(str(config_file))

        assert config["database"]["url"] == "sqlite:///test.db"
        assert config["logging"]["level"] == "INFO"

    def test_load_config_file_not_found(self):
        """Test handling of missing configuration file."""
        from app.core.config import load_config_from_file

        with pytest.raises(FileNotFoundError):
            load_config_from_file("/nonexistent/config.json")

    def test_load_config_invalid_json(self, temp_dir):
        """Test handling of invalid JSON configuration."""
        from app.core.config import load_config_from_file

        config_file = temp_dir / "invalid_config.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_config_from_file(str(config_file))

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test handling of invalid YAML configuration."""
        from app.core.config import load_config_from_file

        config_file = temp_dir / "invalid_config.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            load_config_from_file(str(config_file))


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_env_var_override(self):
        """Test environment variable override of configuration."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_DATABASE_URL': 'postgresql://env:env@localhost/envdb',
            'FIREWALLO_SECRET_KEY': 'env-secret-key',
            'FIREWALLO_DEBUG': 'false',
            'FIREWALLO_API_PORT': '9000'
        }):
            config = Config()

            assert config.database_url == 'postgresql://env:env@localhost/envdb'
            assert config.secret_key == 'env-secret-key'
            assert config.debug is False
            assert config.api_port == 9000

    def test_env_var_type_conversion(self):
        """Test automatic type conversion for environment variables."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_API_PORT': '8080',
            'FIREWALLO_DEBUG': 'true',
            'FIREWALLO_DATABASE_POOL_SIZE': '20',
            'FIREWALLO_TOKEN_EXPIRE_MINUTES': '120'
        }):
            config = Config()

            assert isinstance(config.api_port, int)
            assert config.api_port == 8080
            assert isinstance(config.debug, bool)
            assert config.debug is True
            assert isinstance(config.database_pool_size, int)
            assert config.database_pool_size == 20

    def test_env_var_boolean_values(self):
        """Test boolean environment variable parsing."""
        from app.core.config import Config

        # Test various boolean representations
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('off', False)
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'FIREWALLO_DEBUG': env_value}):
                config = Config()
                assert config.debug == expected

    def test_env_var_list_parsing(self):
        """Test parsing list values from environment variables."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080,https://example.com',
            'FIREWALLO_ALLOWED_HOSTS': 'localhost,127.0.0.1,0.0.0.0'
        }):
            config = Config()

            assert isinstance(config.cors_origins, list)
            assert len(config.cors_origins) == 3
            assert 'http://localhost:3000' in config.cors_origins
            assert 'https://example.com' in config.cors_origins

    def test_env_var_prefix_handling(self):
        """Test environment variable prefix handling."""
        from app.core.config import Config

        # Test both prefixed and non-prefixed variables
        with patch.dict(os.environ, {
            'FIREWALLO_SECRET_KEY': 'prefixed-key',
            'SECRET_KEY': 'non-prefixed-key',
            'DATABASE_URL': 'non-prefixed-db',
            'FIREWALLO_DATABASE_URL': 'prefixed-db'
        }):
            config = Config()

            # Prefixed variables should take precedence
            assert config.secret_key == 'prefixed-key'
            assert config.database_url == 'prefixed-db'


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_required_fields_validation(self):
        """Test validation of required configuration fields."""
        from app.core.config import Config, ConfigValidationError

        # Test missing secret key
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigValidationError) as exc_info:
                config = Config()
                config.validate()

            assert "secret_key" in str(exc_info.value).lower()

    def test_database_url_validation(self):
        """Test database URL validation."""
        from app.core.config import Config, ConfigValidationError

        # Test invalid database URL
        invalid_urls = [
            "invalid-url",
            "http://not-a-database",
            "ftp://invalid-scheme",
            ""
        ]

        for invalid_url in invalid_urls:
            with patch.dict(os.environ, {'FIREWALLO_DATABASE_URL': invalid_url}):
                config = Config()
                with pytest.raises(ConfigValidationError):
                    config.validate_database_url()

    def test_port_number_validation(self):
        """Test port number validation."""
        from app.core.config import Config, ConfigValidationError

        # Test invalid port numbers
        invalid_ports = [-1, 0, 65536, 100000]

        for invalid_port in invalid_ports:
            with patch.dict(os.environ, {'FIREWALLO_API_PORT': str(invalid_port)}):
                config = Config()
                with pytest.raises(ConfigValidationError):
                    config.validate_port_numbers()

    def test_secret_key_strength_validation(self):
        """Test secret key strength validation."""
        from app.core.config import Config, ConfigValidationError

        # Test weak secret keys
        weak_keys = [
            "short",
            "12345678",
            "password",
            "abcdefgh"
        ]

        for weak_key in weak_keys:
            with patch.dict(os.environ, {'FIREWALLO_SECRET_KEY': weak_key}):
                config = Config()
                with pytest.raises(ConfigValidationError):
                    config.validate_secret_key_strength()

    def test_log_level_validation(self):
        """Test log level validation."""
        from app.core.config import Config, ConfigValidationError

        # Test invalid log levels
        invalid_levels = ["INVALID", "TRACE", "VERBOSE", ""]

        for invalid_level in invalid_levels:
            with patch.dict(os.environ, {'FIREWALLO_LOG_LEVEL': invalid_level}):
                config = Config()
                with pytest.raises(ConfigValidationError):
                    config.validate_log_level()

    def test_valid_configuration(self):
        """Test validation with valid configuration."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_SECRET_KEY': 'very-secure-secret-key-for-testing-purposes-only',
            'FIREWALLO_DATABASE_URL': 'postgresql://user:pass@localhost/db',
            'FIREWALLO_API_PORT': '8000',
            'FIREWALLO_LOG_LEVEL': 'INFO'
        }):
            config = Config()

            # Should not raise any exceptions
            config.validate()
            assert config.is_valid()


class TestConfigurationMerging:
    """Test configuration merging and precedence."""

    def test_config_precedence_order(self, temp_dir):
        """Test configuration precedence: env vars > config file > defaults."""
        from app.core.config import merge_configs

        # Default config
        default_config = {
            "database": {"url": "sqlite:///default.db", "pool_size": 5},
            "api": {"host": "localhost", "port": 8000},
            "auth": {"secret_key": "default-key"}
        }

        # File config
        file_config = {
            "database": {"url": "postgresql://file:file@localhost/filedb"},
            "api": {"port": 8080},
            "auth": {"secret_key": "file-key", "algorithm": "HS256"}
        }

        # Environment config
        env_config = {
            "database": {"url": "postgresql://env:env@localhost/envdb"},
            "auth": {"secret_key": "env-key"}
        }

        merged = merge_configs(default_config, file_config, env_config)

        # Environment should take precedence
        assert merged["database"]["url"] == "postgresql://env:env@localhost/envdb"
        assert merged["auth"]["secret_key"] == "env-key"

        # File config should override defaults
        assert merged["api"]["port"] == 8080
        assert merged["auth"]["algorithm"] == "HS256"

        # Defaults should be used when not overridden
        assert merged["database"]["pool_size"] == 5
        assert merged["api"]["host"] == "localhost"

    def test_deep_merge_configuration(self):
        """Test deep merging of nested configuration objects."""
        from app.core.config import deep_merge_configs

        base_config = {
            "database": {
                "url": "sqlite:///base.db",
                "pool_size": 5,
                "options": {
                    "timeout": 30,
                    "retry": 3
                }
            },
            "logging": {
                "level": "INFO",
                "handlers": ["console"]
            }
        }

        override_config = {
            "database": {
                "pool_size": 10,
                "options": {
                    "timeout": 60
                }
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(message)s"
            },
            "new_section": {
                "enabled": True
            }
        }

        merged = deep_merge_configs(base_config, override_config)

        # Check deep merging
        assert merged["database"]["url"] == "sqlite:///base.db"  # Unchanged
        assert merged["database"]["pool_size"] == 10  # Overridden
        assert merged["database"]["options"]["timeout"] == 60  # Overridden
        assert merged["database"]["options"]["retry"] == 3  # Unchanged

        assert merged["logging"]["level"] == "DEBUG"  # Overridden
        assert merged["logging"]["handlers"] == ["console"]  # Unchanged
        assert merged["logging"]["format"] == "%(asctime)s - %(message)s"  # New

        assert merged["new_section"]["enabled"] is True  # New section


class TestConfigurationSecurity:
    """Test configuration security features."""

    def test_sensitive_data_masking(self):
        """Test masking of sensitive configuration data."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_SECRET_KEY': 'very-secret-key',
            'FIREWALLO_DATABASE_URL': 'postgresql://user:password@localhost/db',
            'FIREWALLO_API_KEY': 'sensitive-api-key'
        }):
            config = Config()

            # Get masked configuration
            masked_config = config.to_dict(mask_sensitive=True)

            assert masked_config['secret_key'] == '***MASKED***'
            assert 'password' not in masked_config['database_url']
            assert '***MASKED***' in masked_config['database_url']
            assert masked_config['api_key'] == '***MASKED***'

    def test_configuration_export_without_secrets(self):
        """Test exporting configuration without sensitive data."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_SECRET_KEY': 'very-secret-key',
            'FIREWALLO_DATABASE_URL': 'postgresql://user:password@localhost/db',
            'FIREWALLO_DEBUG': 'true',
            'FIREWALLO_API_PORT': '8000'
        }):
            config = Config()

            # Export safe configuration
            safe_config = config.export_safe()

            assert 'secret_key' not in safe_config
            assert 'database_url' not in safe_config
            assert safe_config['debug'] is True
            assert safe_config['api_port'] == 8000

    def test_configuration_validation_security(self):
        """Test security-related configuration validation."""
        from app.core.config import Config, SecurityValidationError

        # Test insecure configurations
        insecure_configs = [
            {'FIREWALLO_DEBUG': 'true', 'FIREWALLO_ENV': 'production'},  # Debug in production
            {'FIREWALLO_SECRET_KEY': 'default'},  # Default secret key
            {'FIREWALLO_API_HOST': '0.0.0.0', 'FIREWALLO_DEBUG': 'true'},  # Public debug
        ]

        for insecure_config in insecure_configs:
            with patch.dict(os.environ, insecure_config):
                config = Config()
                with pytest.raises(SecurityValidationError):
                    config.validate_security()


class TestConfigurationDynamicReloading:
    """Test dynamic configuration reloading."""

    def test_reload_configuration_from_file(self, temp_dir):
        """Test reloading configuration from file."""
        from app.core.config import ConfigManager

        # Create initial config file
        config_file = temp_dir / "dynamic_config.json"
        initial_config = {
            "api": {"port": 8000},
            "logging": {"level": "INFO"}
        }

        with open(config_file, 'w') as f:
            json.dump(initial_config, f)

        # Create config manager
        config_manager = ConfigManager(config_file)
        config = config_manager.load()

        assert config["api"]["port"] == 8000
        assert config["logging"]["level"] == "INFO"

        # Update config file
        updated_config = {
            "api": {"port": 8080},
            "logging": {"level": "DEBUG"}
        }

        with open(config_file, 'w') as f:
            json.dump(updated_config, f)

        # Reload configuration
        reloaded_config = config_manager.reload()

        assert reloaded_config["api"]["port"] == 8080
        assert reloaded_config["logging"]["level"] == "DEBUG"

    def test_configuration_change_notifications(self, temp_dir):
        """Test configuration change notifications."""
        from app.core.config import ConfigManager

        config_file = temp_dir / "notify_config.json"
        initial_config = {"api": {"port": 8000}}

        with open(config_file, 'w') as f:
            json.dump(initial_config, f)

        config_manager = ConfigManager(config_file)

        # Set up change notification
        changes_detected = []

        def on_config_change(old_config, new_config):
            changes_detected.append((old_config, new_config))

        config_manager.on_change(on_config_change)

        # Load initial config
        config_manager.load()

        # Update config
        updated_config = {"api": {"port": 8080}}
        with open(config_file, 'w') as f:
            json.dump(updated_config, f)

        config_manager.reload()

        # Check that change was detected
        assert len(changes_detected) == 1
        old_config, new_config = changes_detected[0]
        assert old_config["api"]["port"] == 8000
        assert new_config["api"]["port"] == 8080

    @patch('app.core.config.os.path.getmtime')
    def test_configuration_file_watching(self, mock_getmtime, temp_dir):
        """Test configuration file modification time watching."""
        from app.core.config import ConfigWatcher

        config_file = temp_dir / "watched_config.json"
        config_data = {"api": {"port": 8000}}

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Mock file modification times
        mock_getmtime.side_effect = [1000, 1000, 2000]  # Initial, check, changed

        watcher = ConfigWatcher(config_file)

        # Initial check - should not detect change
        assert not watcher.has_changed()

        # File modified - should detect change
        assert watcher.has_changed()


class TestConfigurationPerformance:
    """Test configuration system performance."""

    def test_configuration_loading_performance(self, benchmark_config):
        """Test configuration loading performance."""
        from app.core.config import Config

        def load_config():
            return Config()

        # Benchmark configuration loading
        result = benchmark_config(load_config)

        # Should load quickly (within reasonable time)
        assert result is not None

    def test_configuration_validation_performance(self, benchmark_config):
        """Test configuration validation performance."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_SECRET_KEY': 'test-secret-key-for-performance-testing',
            'FIREWALLO_DATABASE_URL': 'postgresql://test:test@localhost/testdb'
        }):
            config = Config()

            def validate_config():
                config.validate()
                return True

            # Benchmark validation
            result = benchmark_config(validate_config)
            assert result is True

    def test_large_configuration_handling(self, temp_dir):
        """Test handling of large configuration files."""
        from app.core.config import load_config_from_file

        # Generate large configuration
        large_config = {
            "sections": {}
        }

        # Create 1000 configuration sections with multiple keys each
        for i in range(1000):
            large_config["sections"][f"section_{i}"] = {
                f"key_{j}": f"value_{i}_{j}" for j in range(10)
            }

        config_file = temp_dir / "large_config.json"
        with open(config_file, 'w') as f:
            json.dump(large_config, f)

        # Should handle large config without issues
        loaded_config = load_config_from_file(str(config_file))

        assert len(loaded_config["sections"]) == 1000
        assert loaded_config["sections"]["section_0"]["key_0"] == "value_0_0"


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def test_full_configuration_workflow(self, temp_dir, mock_env_vars):
        """Test complete configuration workflow."""
        from app.core.config import Config, ConfigManager

        # Create config file
        config_file = temp_dir / "integration_config.json"
        file_config = {
            "database": {"url": "postgresql://file:file@localhost/filedb"},
            "api": {"host": "0.0.0.0", "port": 8080}
        }

        with open(config_file, 'w') as f:
            json.dump(file_config, f)

        # Environment variables should override
        env_overrides = {
            'FIREWALLO_API_PORT': '9000',
            'FIREWALLO_DEBUG': 'false'
        }

        with patch.dict(os.environ, env_overrides):
            # Load configuration with all sources
            config_manager = ConfigManager(config_file)
            config = config_manager.load_with_env_overrides()

            # Verify precedence
            assert config["api"]["port"] == 9000  # From environment
            assert config["api"]["host"] == "0.0.0.0"  # From file
            assert config["debug"] is False  # From environment

            # Validate configuration
            config_obj = Config(config)
            config_obj.validate()

            # Export safe version
            safe_config = config_obj.export_safe()
            assert 'database' not in safe_config  # Sensitive data excluded

    def test_configuration_with_plugins(self, mock_plugin_manager):
        """Test configuration integration with plugin system."""
        from app.core.config import Config

        with patch.dict(os.environ, {
            'FIREWALLO_PLUGINS_ENABLED': 'true',
            'FIREWALLO_PLUGINS_AUTO_LOAD': 'false',
            'FIREWALLO_PLUGINS_DIRECTORIES': '/app/plugins,/opt/plugins'
        }):
            config = Config()

            assert config.plugins_enabled is True
            assert config.plugins_auto_load is False
            assert isinstance(config.plugins_directories, list)
            assert len(config.plugins_directories) == 2
            assert '/app/plugins' in config.plugins_directories

    def test_configuration_database_integration(self, mock_database):
        """Test configuration integration with database."""
        from app.core.config import Config, save_config_to_database

        config = Config()

        # Save configuration to database
        config_dict = config.to_dict(mask_sensitive=True)
        save_config_to_database(config_dict)

        # Verify database calls were made
        mock_database.execute.assert_called()

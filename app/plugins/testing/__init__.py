"""Testing utilities for the Firewallo Plugin Framework.

This module provides base classes and utilities for testing plugins,
including test fixtures, mocks, and helper functions.
"""

from .base import (
    PluginTestCase,
    AsyncPluginTestCase,
    MockPluginManager,
    MockRepository,
    TestPlugin,
    create_test_plugin,
    load_test_manifest,
    validate_test_plugin,
)

__all__ = [
    # Base test classes
    "PluginTestCase",
    "AsyncPluginTestCase",

    # Mock objects
    "MockPluginManager",
    "MockRepository",

    # Test utilities
    "TestPlugin",
    "create_test_plugin",
    "load_test_manifest",
    "validate_test_plugin",
]

"""
Firewallo UI Test Suite

This package contains all tests for the Firewallo UI application.

Test Structure:
- test_api/: API endpoint tests
- test_auth/: Authentication and authorization tests
- test_core/: Core application functionality tests
- test_db/: Database layer tests
- test_plugins_system/: Plugin system framework tests
- test_users/: User management tests

Test Categories:
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions
- API tests: Test HTTP endpoints and responses
- Plugin tests: Test plugin system functionality
- E2E tests: End-to-end application testing

Usage:
    # Run all tests
    pytest tests/

    # Run specific test category
    pytest tests/ -m "unit"
    pytest tests/ -m "api"
    pytest tests/ -m "integration"

    # Run tests with coverage
    pytest tests/ --cov=app --cov-report=html

    # Run tests in parallel
    pytest tests/ -n auto

    # Run specific test module
    pytest tests/test_api/test_system.py

    # Run with verbose output
    pytest tests/ -v -s

Configuration:
    Test configuration is defined in pytest.ini
    Shared fixtures and utilities are in conftest.py
    Test requirements are in requirements.txt

Environment:
    Tests should run in isolation and not affect production data.
    Use the FIREWALLO_ENV=test environment variable.
    Mock external dependencies and services.

Contributing:
    - Follow the existing test structure and patterns
    - Use descriptive test names that explain what is being tested
    - Include both positive and negative test cases
    - Mock external dependencies appropriately
    - Add docstrings to test classes and complex test functions
    - Use appropriate pytest markers for test categorization
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"
__author__ = "Firewallo Development Team"
__description__ = "Test suite for Firewallo UI application"

# Test configuration constants
TEST_CONFIG = {
    "database_url": "sqlite:///test.db",
    "secret_key": "test-secret-key-for-testing-only",
    "debug": True,
    "testing": True,
    "log_level": "DEBUG"
}

# Test data directories
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_FIXTURES_DIR.mkdir(exist_ok=True)
TEST_OUTPUTS_DIR.mkdir(exist_ok=True)

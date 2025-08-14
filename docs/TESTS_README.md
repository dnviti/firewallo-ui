# Firewallo UI Testing Infrastructure

This directory contains the comprehensive testing infrastructure for the Firewallo UI project, including tests for the main application, plugin system, and individual plugins.

## Table of Contents

- [Testing Structure](#testing-structure)
- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Plugin Testing](#plugin-testing)
- [Test Configuration](#test-configuration)
- [Coverage Reports](#coverage-reports)
- [Writing Tests](#writing-tests)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Testing Structure

```
firewallo-ui/
├── tests/                          # Main application tests
│   ├── __init__.py
│   ├── pytest.ini                  # Main test configuration
│   ├── conftest.py                  # Shared fixtures and utilities
│   ├── requirements.txt             # Test dependencies
│   ├── run_all_tests.py            # Master test runner
│   ├── README.md                   # This file
│   ├── test_api/                   # API endpoint tests
│   │   ├── test_auth.py
│   │   ├── test_plugins.py
│   │   ├── test_system.py
│   │   └── test_webui_*.py
│   ├── test_auth/                  # Authentication tests
│   ├── test_core/                  # Core functionality tests
│   │   └── test_config.py
│   ├── test_db/                    # Database tests
│   ├── test_plugins_system/        # Plugin framework tests
│   │   ├── test_manager.py
│   │   └── test_integration.py
│   └── test_users/                 # User management tests
└── app/plugins/                    # Plugin-specific tests
    ├── system/webui/tests/         # WebUI plugin tests (example)
    │   ├── pytest.ini
    │   ├── run_tests.py
    │   └── test_*.py
    └── vpn/wireguard/tests/        # WireGuard plugin tests
        ├── pytest.ini
        ├── run_tests.py
        ├── test_plugin.py
        └── test_*.py
```

## Quick Start

### 1. Install Test Dependencies

```bash
# Install required test packages
pip install -r tests/requirements.txt

# Or install specific packages
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx
```

### 2. Run All Tests

```bash
# Run all tests (main app + plugins)
python tests/run_all_tests.py

# Run with verbose output and coverage
python tests/run_all_tests.py -v --coverage

# Run tests in parallel (faster)
python tests/run_all_tests.py --parallel
```

### 3. Check Results

```bash
# Check test coverage report
open tests/coverage_html/index.html

# View test results summary
cat test_results.json
```

## Test Categories

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- High coverage of business logic

```bash
# Run unit tests only
pytest tests/ -m unit
```

### Integration Tests
- Test component interactions
- Use real or test databases
- Test API endpoints end-to-end
- Verify plugin system integration

```bash
# Run integration tests only
pytest tests/ -m integration
```

### API Tests
- Test HTTP endpoints
- Validate request/response formats
- Test authentication and authorization
- Error handling validation

```bash
# Run API tests only
pytest tests/ -m api
```

### Plugin Tests
- Test plugin lifecycle (load/unload/enable/disable)
- Test plugin isolation and sandboxing
- Validate plugin APIs and configurations
- Test plugin dependencies

```bash
# Run plugin system tests
pytest tests/test_plugins_system/

# Run specific plugin tests
pytest app/plugins/vpn/wireguard/tests/
```

## Running Tests

### Main Test Runner

The main test runner (`tests/run_all_tests.py`) provides comprehensive testing capabilities:

```bash
# Basic usage
python tests/run_all_tests.py [OPTIONS]

# Common options
--verbose, -v           # Verbose output
--coverage              # Generate coverage report
--parallel              # Run tests in parallel
--main-only             # Run only main app tests
--plugins-only          # Run only plugin tests
--integration           # Run only integration tests
--check-deps            # Check test dependencies
--cleanup               # Clean up test artifacts
--json-output FILE      # Save results to JSON file
```

### Examples

```bash
# Quick test run
python tests/run_all_tests.py

# Full test suite with coverage
python tests/run_all_tests.py -v --coverage --parallel

# Only plugin tests
python tests/run_all_tests.py --plugins-only

# Only integration tests
python tests/run_all_tests.py --integration

# Check dependencies
python tests/run_all_tests.py --check-deps

# Clean up test artifacts
python tests/run_all_tests.py --cleanup
```

### Direct Pytest Usage

You can also run tests directly with pytest:

```bash
# Run all main app tests
pytest tests/

# Run specific test file
pytest tests/test_api/test_auth.py

# Run specific test function
pytest tests/test_api/test_auth.py::TestLoginEndpoints::test_login_success

# Run with markers
pytest tests/ -m "api and not slow"

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run in parallel
pytest tests/ -n auto
```

## Plugin Testing

### Plugin Test Structure

Each plugin should have its own `tests` directory following this structure:

```
plugin_name/
├── tests/
│   ├── __init__.py              # Test package initialization
│   ├── pytest.ini              # Plugin-specific test config
│   ├── run_tests.py            # Plugin test runner
│   ├── test_plugin.py          # Main plugin functionality tests
│   ├── test_api.py             # Plugin API tests
│   ├── test_integration.py     # Integration tests
│   └── test_services.py        # Service layer tests
├── plugin.py                   # Main plugin file
├── services.py                 # Plugin services
└── manifest.json              # Plugin manifest
```

### Running Plugin Tests

```bash
# Run tests for specific plugin
cd app/plugins/vpn/wireguard/tests
python run_tests.py

# Or use pytest directly
pytest app/plugins/vpn/wireguard/tests/

# Run with coverage for plugin only
pytest app/plugins/vpn/wireguard/tests/ --cov=../plugin.py --cov=../services.py
```

### Plugin Test Guidelines

1. **Isolation**: Plugin tests should be completely self-contained
2. **Mocking**: Mock external dependencies and system calls
3. **Configuration**: Test all configuration scenarios
4. **Error Handling**: Test error conditions and recovery
5. **API Coverage**: Test all plugin API endpoints
6. **Security**: Test permission and security validations

## Test Configuration

### Main Configuration (`tests/pytest.ini`)

```ini
[tool:pytest]
python_files = test_*.py *_test.py
python_classes = Test* *Tests
python_functions = test_*
testpaths = .
minversion = 6.0
addopts = --strict-markers --strict-config --verbose
markers =
    unit: Unit tests
    integration: Integration tests
    api: API endpoint tests
    slow: Slow tests (> 5 seconds)
    asyncio: Async tests
```

### Environment Variables

Set these environment variables for testing:

```bash
export FIREWALLO_ENV=test
export DATABASE_URL=sqlite:///test.db
export SECRET_KEY=test-secret-key-for-testing-only
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Test Database

Tests use a separate test database to avoid affecting production data:

```bash
# Automatic test database setup
# - SQLite in-memory database for unit tests
# - Temporary PostgreSQL database for integration tests
# - Automatic cleanup after tests
```

## Coverage Reports

### Generating Coverage

```bash
# Generate HTML coverage report
python tests/run_all_tests.py --coverage

# View coverage report
open tests/coverage_html/index.html

# Generate coverage summary
pytest tests/ --cov=app --cov-report=term-missing
```

### Coverage Targets

- **Overall Coverage**: > 85%
- **API Endpoints**: > 90%
- **Core Functions**: > 95%
- **Plugin System**: > 80%
- **Individual Plugins**: > 85%

### Excluded from Coverage

- Static files and templates
- Migration files
- Test files themselves
- Third-party integrations (mocked)
- Debug and development utilities

## Writing Tests

### Test Structure

```python
#!/usr/bin/env python3
"""
Description of what this test module covers.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

# Test markers
pytestmark = [pytest.mark.api, pytest.mark.asyncio]

class TestFeatureName:
    """Test class for specific feature."""

    async def test_success_case(self, test_client):
        """Test successful operation."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        result = await some_function(test_data)
        
        # Assert
        assert result is not None
        assert result["status"] == "success"

    async def test_error_case(self, test_client):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            await some_function(invalid_data)
```

### Fixtures

Use fixtures for common test setup:

```python
@pytest.fixture
async def mock_service():
    """Mock service for testing."""
    service = AsyncMock()
    service.get_data.return_value = {"test": "data"}
    return service

@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com"
    }
```

### Async Testing

For async functions:

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

### Mocking

Mock external dependencies:

```python
@patch('app.external_service.call_api')
async def test_with_mock(mock_api_call):
    """Test with mocked external service."""
    mock_api_call.return_value = {"status": "ok"}
    
    result = await function_that_calls_api()
    
    assert result["status"] == "ok"
    mock_api_call.assert_called_once()
```

## Best Practices

### Test Organization

1. **One test class per feature/component**
2. **Descriptive test names**: `test_should_create_user_when_valid_data_provided`
3. **Arrange-Act-Assert pattern**
4. **Test both positive and negative cases**
5. **Use meaningful assertions**

### Test Data

1. **Use fixtures for reusable test data**
2. **Generate data programmatically when possible**
3. **Keep test data minimal and focused**
4. **Clean up test data after tests**

### Async Testing

1. **Mark async tests with `@pytest.mark.asyncio`**
2. **Use `AsyncMock` for async mocked objects**
3. **Test async context managers properly**
4. **Handle async exceptions correctly**

### Performance

1. **Keep unit tests fast (< 1 second)**
2. **Use `@pytest.mark.slow` for slow tests**
3. **Mock external services to avoid network delays**
4. **Run tests in parallel when possible**

### Security Testing

1. **Test authentication and authorization**
2. **Validate input sanitization**
3. **Test rate limiting and abuse protection**
4. **Verify sensitive data masking**

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Fix Python path issues
export PYTHONPATH=/path/to/firewallo-ui:$PYTHONPATH

# Or run from project root
cd /path/to/firewallo-ui
python tests/run_all_tests.py
```

#### Database Errors
```bash
# Reset test database
rm test.db
python tests/run_all_tests.py

# Check database permissions
ls -la test.db
```

#### Async Test Issues
```python
# Ensure proper async test marking
@pytest.mark.asyncio
async def test_async_function():
    # Use AsyncMock for async mocks
    mock_service = AsyncMock()
    mock_service.async_method.return_value = "result"
```

#### Plugin Test Issues
```bash
# Run plugin tests from correct directory
cd app/plugins/plugin_name/tests
python run_tests.py

# Check plugin dependencies
python -c "import plugin; print('Plugin imports OK')"
```

### Debug Mode

Enable debug output:

```bash
# Verbose pytest output
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ --tb=long --showlocals

# Debug specific test
pytest tests/test_file.py::test_function -v -s --pdb
```

### Performance Issues

```bash
# Profile test execution
pytest tests/ --durations=10

# Run subset of tests
pytest tests/test_api/ -k "not slow"

# Use parallel execution
pytest tests/ -n auto
```

## Continuous Integration

### GitHub Actions

The project includes GitHub Actions workflow for automated testing:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run tests
        run: python tests/run_all_tests.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

Install pre-commit hooks to run tests before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Contributing

### Adding New Tests

1. **Identify the component/feature to test**
2. **Choose the appropriate test directory**
3. **Follow existing test patterns**
4. **Write comprehensive test cases**
5. **Ensure tests pass in isolation**
6. **Update documentation if needed**

### Test Review Checklist

- [ ] Tests cover both success and failure cases
- [ ] External dependencies are properly mocked
- [ ] Tests are fast and reliable
- [ ] Test names are descriptive
- [ ] Code coverage meets requirements
- [ ] Tests follow project conventions
- [ ] Documentation is updated

### Reporting Issues

When reporting test-related issues:

1. **Include full error output**
2. **Specify Python version and OS**
3. **List installed package versions**
4. **Provide steps to reproduce**
5. **Include relevant configuration**

## Support

For questions about testing:

1. **Check this documentation first**
2. **Review existing test code for examples**
3. **Check the project's issue tracker**
4. **Ask in project discussions**

---

**Happy Testing! 🧪**

Remember: Good tests make good software. Invest time in writing comprehensive, maintainable tests that will catch bugs before they reach production.
# Contributing to Firewallo

Thank you for your interest in contributing to Firewallo! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **🐛 Bug Reports** - Help us identify and fix issues
- **✨ Feature Requests** - Suggest new functionality
- **📚 Documentation** - Improve or expand documentation
- **🔌 Plugins** - Develop new plugins for network management
- **🧪 Tests** - Add or improve test coverage
- **🔧 Code** - Fix bugs or implement features

## 🚀 Getting Started

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/firewallo-ui.git
   cd firewallo-ui
   ```

2. **Set up development environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r tests/requirements.txt
   ```

3. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Development Environment

- **Python**: 3.8 or higher
- **IDE**: VS Code, PyCharm, or your preferred editor
- **Browser**: For testing API docs at http://localhost:8000/docs

## 📝 Development Guidelines

### Code Style

- **PEP 8**: Follow Python's official style guide
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Document all public functions and classes
- **Line Length**: Maximum 88 characters (Black formatter standard)

### Code Formatting

We use automated formatting tools:

```bash
# Install formatting tools
pip install black isort flake8

# Format code
black app/ tests/
isort app/ tests/

# Check code style
flake8 app/ tests/
```

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(plugins): add OpenVPN plugin support
fix(auth): resolve JWT token expiration issue
docs(api): update authentication documentation
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_plugins/test_plugin_manager.py

# Run tests with verbose output
pytest -v
```

### Writing Tests

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **API Tests**: Test API endpoints
- **Plugin Tests**: Test plugin functionality

**Test Structure:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_endpoint():
    """Test API endpoint functionality."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test Coverage

- Maintain **minimum 80%** test coverage
- All new features must include tests
- Bug fixes should include regression tests

## 🔌 Plugin Development

### Plugin Structure

```
plugin_name/
├── __init__.py
├── plugin.py          # Main plugin class
├── models.py          # Data models
├── routes.py          # API routes (if needed)
├── config.py          # Configuration
├── docs/              # Plugin documentation
│   └── README.md
└── tests/             # Plugin tests
    └── test_plugin.py
```

### Plugin Guidelines

- **Base Classes**: Inherit from appropriate base plugin classes
- **Documentation**: Include comprehensive README in `docs/`
- **Configuration**: Use Pydantic models for configuration
- **Error Handling**: Implement proper error handling and logging
- **Testing**: Include unit and integration tests

### Plugin Template

```python
from app.plugins.base import BasePlugin
from pydantic import BaseModel

class PluginConfig(BaseModel):
    enabled: bool = True
    # Add your configuration fields

class YourPlugin(BasePlugin):
    def __init__(self, config: PluginConfig):
        super().__init__("your-plugin", "1.0.0")
        self.config = config
    
    async def initialize(self):
        """Initialize plugin resources."""
        pass
    
    async def cleanup(self):
        """Cleanup plugin resources."""
        pass
```

## 📋 Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add or update tests** for your changes
3. **Run the test suite** and ensure all tests pass
4. **Format your code** using Black and isort
5. **Update CHANGELOG.md** if applicable

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Plugin development

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Breaking changes documented
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: Maintainers review code quality and design
3. **Testing**: Manual testing of new features
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge into main branch

## 🐛 Bug Reports

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to ensure bug still exists
3. **Gather information** about your environment

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.2]
- Firewallo version: [e.g., 1.0.0]
- Browser: [if applicable]

## Additional Context
Screenshots, logs, or other relevant information
```

## ✨ Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other solutions you've considered

## Additional Context
Mockups, examples, or references
```

## 📚 Documentation

### Documentation Standards

- **Clear Language**: Write for users with varying technical backgrounds
- **Examples**: Include practical examples and code snippets
- **Screenshots**: Use screenshots for UI-related documentation
- **Links**: Cross-reference related documentation
- **Updates**: Keep documentation current with code changes

### Documentation Structure

```
docs/
├── INDEX.md                    # Documentation index
├── PLUGIN_FRAMEWORK.md         # Plugin framework guide
├── PLUGIN_DEVELOPMENT.md       # Plugin development guide
├── DATABASE_ARCHITECTURE.md    # Database design
├── API_REFERENCE.md           # API documentation
└── images/                    # Documentation images
```

## 🏷️ Release Process

### Version Numbers

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Create release branch
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release tag
- [ ] Build and publish Docker images

## 🎯 Code of Conduct

### Our Standards

- **Respectful**: Be respectful and inclusive
- **Constructive**: Provide constructive feedback
- **Collaborative**: Work together toward common goals
- **Professional**: Maintain professional communication

### Unacceptable Behavior

- Harassment or discrimination
- Inappropriate comments or imagery
- Trolling or insulting behavior
- Publishing private information

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **API Documentation**: `/docs` endpoint for API reference
- **Documentation**: Check `/docs` folder for guides

### Response Times

- **Bug Reports**: 2-3 business days
- **Feature Requests**: 1 week
- **Pull Requests**: 3-5 business days
- **Security Issues**: 24-48 hours

## 🙏 Recognition

Contributors are recognized in:
- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Major contributors mentioned
- **Documentation**: Author attribution where appropriate

## 📄 License

By contributing to Firewallo, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Firewallo! Your efforts help make network management more accessible and powerful for everyone.
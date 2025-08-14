"""
Plugin system tests package for Firewallo UI.

This package contains tests for the plugin framework and plugin management functionality.

Test modules:
- test_manager.py: Plugin manager tests
- test_loader.py: Plugin loader tests
- test_validator.py: Plugin validation tests
- test_registry.py: Plugin registry tests
- test_integration.py: Plugin system integration tests
- test_sandbox.py: Plugin sandboxing tests
- test_events.py: Plugin event system tests
- test_dependencies.py: Plugin dependency resolution tests
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

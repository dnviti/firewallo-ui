"""Tests for the Firewallo WebUI Plugin.

This package contains all test modules for the WebUI plugin, including:
- Unit tests for plugin functionality
- Integration tests with the plugin framework
- API endpoint tests
- Service layer tests
- Configuration validation tests
"""

import sys
import os
from pathlib import Path

# Add the plugin directory to Python path for testing
plugin_dir = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_dir))

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(app_dir))

__version__ = "2.0.0"
__author__ = "Firewallo Team"

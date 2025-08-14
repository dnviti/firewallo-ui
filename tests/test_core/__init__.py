"""
Core tests package for Firewallo UI.

This package contains tests for core application functionality.

Test modules:
- test_config.py: Configuration management tests
- test_startup.py: Application startup and initialization tests
- test_health.py: Health checking system tests
- test_logging.py: Logging system tests
- test_security.py: Security utilities tests
- test_utils.py: Core utility function tests
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

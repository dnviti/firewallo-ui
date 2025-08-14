"""
API tests package for Firewallo UI.

This package contains tests for all API endpoints and related functionality.

Test modules:
- test_auth.py: Authentication and authorization API tests
- test_plugins.py: Plugin management API tests
- test_system.py: System information and health API tests
- test_webui_integration.py: Web UI integration tests
- test_webui_final.py: Final web UI validation tests
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

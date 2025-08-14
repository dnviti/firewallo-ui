"""
Authentication tests package for Firewallo UI.

This package contains tests for authentication and authorization functionality.

Test modules:
- test_jwt_handler.py: JWT token handling tests
- test_password_manager.py: Password management tests
- test_session_manager.py: Session management tests
- test_permissions.py: Permission system tests
- test_middleware.py: Authentication middleware tests
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

"""
Users tests package for Firewallo UI.

This package contains tests for user management functionality.

Test modules:
- test_user_manager.py: User creation, update, deletion tests
- test_user_authentication.py: User authentication tests
- test_user_permissions.py: User permission and role tests
- test_user_profiles.py: User profile management tests
- test_user_sessions.py: User session management tests
- test_user_validation.py: User data validation tests
- test_user_security.py: User security features tests
- test_user_api.py: User management API endpoint tests
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

"""
Database tests package for Firewallo UI.

This package contains tests for database functionality and data persistence.

Test modules:
- test_database.py: Database connection and basic operations tests
- test_models.py: Data model validation and ORM tests
- test_migrations.py: Database migration tests
- test_transactions.py: Transaction handling tests
- test_connection_pool.py: Connection pooling tests
- test_backup_restore.py: Database backup and restore tests
- test_performance.py: Database performance tests
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

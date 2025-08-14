"""Database migration utilities.

Provides functionality to migrate from old flat structure to new modular structure.
"""

import json
import os
from typing import Dict, Any

def migrate_database_structure(db_file_path: str) -> bool:
    """
    Migrate database from old flat structure to new modular structure.
    
    Old structure:
    {
        "servers": [...],
        "peers": [...], 
        "users": [...]
    }
    
    New structure:
    {
        "plugins": {
            "vpn": {
                "wireguard": {
                    "servers": [...],
                    "peers": [...]
                }
            }
        },
        "core": {
            "system": {},
            "config": {},
            "logs": []
        },
        "auth": {
            "users": [...],
            "rbac": {
                "roles": [],
                "permissions": [],
                "assignments": []
            }
        }
    }
    
    Returns True if migration was performed, False if already in new format.
    """
    if not os.path.exists(db_file_path):
        return False
        
    with open(db_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check if migration is needed
    if "plugins" in data and "auth" in data and "core" in data:
        print("Database is already in new modular format")
        return False
    
    # Check if old format
    if not ("servers" in data or "peers" in data or "users" in data):
        print("Database format not recognized")
        return False
    
    print("Migrating database to new modular structure...")
    
    # Create new modular structure
    new_data = {
        "plugins": {
            "vpn": {
                "wireguard": {
                    "servers": data.get("servers", []),
                    "peers": data.get("peers", [])
                }
            }
        },
        "core": {
            "system": {},
            "config": {},
            "logs": []
        },
        "auth": {
            "users": data.get("users", []),
            "rbac": {
                "roles": [],
                "permissions": [],
                "assignments": []
            }
        }
    }
    
    # Backup old file
    backup_path = f"{db_file_path}.backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Backup created at: {backup_path}")
    
    # Write new structure
    with open(db_file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2)
    
    print("Database migration completed successfully")
    return True

def validate_database_structure(db_file_path: str) -> Dict[str, Any]:
    """
    Validate that the database has the expected modular structure.
    
    Returns a validation report with sections found and any issues.
    """
    if not os.path.exists(db_file_path):
        return {"valid": False, "error": "Database file not found"}
    
    try:
        with open(db_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"Invalid JSON: {e}"}
    
    validation_report = {
        "valid": True,
        "sections": {},
        "warnings": [],
        "errors": []
    }
    
    # Validate required sections
    required_sections = ["plugins", "core", "auth"]
    for section in required_sections:
        if section not in data:
            validation_report["errors"].append(f"Missing '{section}' section")
    
    # Validate plugins structure
    if "plugins" in data:
        validation_report["sections"]["plugins"] = _validate_plugins_section(data["plugins"])
    
    # Validate core structure  
    if "core" in data:
        validation_report["sections"]["core"] = _validate_core_section(data["core"])
    
    # Validate auth structure
    if "auth" in data:
        validation_report["sections"]["auth"] = _validate_auth_section(data["auth"])
    
    if validation_report["errors"]:
        validation_report["valid"] = False
    
    return validation_report

def _validate_plugins_section(plugins_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate plugins section structure."""
    result = {}
    if "vpn" in plugins_data and "wireguard" in plugins_data["vpn"]:
        wg = plugins_data["vpn"]["wireguard"]
        result["vpn_wireguard"] = {
            "servers": len(wg.get("servers", [])),
            "peers": len(wg.get("peers", []))
        }
    return result

def _validate_core_section(core_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate core section structure."""
    return {
        "system": "present" if "system" in core_data else "missing",
        "config": "present" if "config" in core_data else "missing",
        "logs": len(core_data.get("logs", []))
    }

def _validate_auth_section(auth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate auth section structure."""
    result = {}
    if "users" in auth_data:
        result["users"] = len(auth_data["users"])
    if "rbac" in auth_data:
        rbac = auth_data["rbac"]
        result["rbac"] = {
            "roles": len(rbac.get("roles", [])),
            "permissions": len(rbac.get("permissions", [])),
            "assignments": len(rbac.get("assignments", []))
        }
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python migration.py <db_file_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    # Run migration
    migrated = migrate_database_structure(db_path)
    
    # Validate structure
    validation_result = validate_database_structure(db_path)
    
    print("\nValidation Report:")
    print(f"Valid: {validation_result['valid']}")
    
    if validation_result.get("sections"):
        print("\nSections found:")
        print(json.dumps(validation_result["sections"], indent=2))
    
    if validation_result.get("warnings"):
        print("\nWarnings:")
        for warning in validation_result["warnings"]:
            print(f"  - {warning}")
    
    if validation_result.get("errors"):
        print("\nErrors:")
        for error in validation_result["errors"]:
            print(f"  - {error}")

#!/usr/bin/env python3
"""
Test script for Firewallo Web UI
Verifies that the web interface components work correctly.
"""

import asyncio
import sys
import os
import time
import subprocess
import requests
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from app.main import app
        from app.api.routes import auth, plugins, gui, system
        from app.core.config import create_app
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_app_creation():
    """Test that the FastAPI app can be created."""
    print("Testing app creation...")
    try:
        from app.main import app
        print(f"✓ FastAPI app created successfully")
        print(f"  - App type: {type(app)}")
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False

def test_static_files():
    """Test that static files exist."""
    print("Testing static files...")
    static_dir = Path("app/static")
    required_files = [
        "css/custom.css",
        "js/common.js"
    ]

    all_exist = True
    for file_path in required_files:
        full_path = static_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False

    return all_exist

def test_templates():
    """Test that template files exist."""
    print("Testing template files...")
    templates_dir = Path("app/templates")
    required_templates = [
        "base.html",
        "dashboard.html",
        "plugins.html",
        "login.html"
    ]

    all_exist = True
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            print(f"✓ {template} exists")
        else:
            print(f"✗ {template} missing")
            all_exist = False

    return all_exist

def test_server_startup():
    """Test that the server can start up."""
    print("Testing server startup...")
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "8001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait a bit for server to start
        time.sleep(3)

        # Check if process is still running
        if process.poll() is None:
            print("✓ Server started successfully")

            # Test basic connectivity
            try:
                response = requests.get("http://127.0.0.1:8001/api/system/health", timeout=5)
                if response.status_code == 200:
                    print("✓ Health endpoint responding")
                    health_data = response.json()
                    print(f"  - Status: {health_data.get('status', 'unknown')}")
                else:
                    print(f"✗ Health endpoint returned status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"✗ Failed to connect to health endpoint: {e}")

            # Test GUI endpoints
            try:
                response = requests.get("http://127.0.0.1:8001/", timeout=5, allow_redirects=False)
                if response.status_code in [200, 302]:
                    print("✓ Root endpoint responding")
                else:
                    print(f"✗ Root endpoint returned status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"✗ Failed to connect to root endpoint: {e}")

            # Test API endpoints
            endpoints_to_test = [
                "/api/system/stats",
                "/api/system/activity/recent",
                "/api/plugins/"
            ]

            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"http://127.0.0.1:8001{endpoint}", timeout=5)
                    if response.status_code == 200:
                        print(f"✓ {endpoint} responding")
                    else:
                        print(f"✗ {endpoint} returned status {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"✗ Failed to connect to {endpoint}: {e}")

            # Terminate server
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Server failed to start")
            print(f"  STDOUT: {stdout.decode()}")
            print(f"  STDERR: {stderr.decode()}")
            return False

    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        return False

def test_template_rendering():
    """Test that templates can be rendered."""
    print("Testing template rendering...")
    try:
        from fastapi.templating import Jinja2Templates
        from fastapi import Request

        templates = Jinja2Templates(directory="app/templates")

        # Create a mock request object
        class MockRequest:
            def __init__(self):
                self.url = "http://localhost:8000/"
                self.headers = {}

        mock_request = MockRequest()

        # Test rendering base template
        try:
            result = templates.TemplateResponse("dashboard.html", {
                "request": mock_request,
                "page_title": "Test Dashboard"
            })
            print("✓ Dashboard template renders successfully")
        except Exception as e:
            print(f"✗ Dashboard template rendering failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"✗ Template rendering test failed: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are available."""
    print("Testing dependencies...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "jinja2",
        "psutil",
        "requests"
    ]

    all_available = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            print(f"✗ {package} not available")
            all_available = False

    return all_available

def main():
    """Run all tests."""
    print("=" * 50)
    print("Firewallo Web UI Test Suite")
    print("=" * 50)

    tests = [
        ("Dependencies", test_dependencies),
        ("Imports", test_imports),
        ("App Creation", test_app_creation),
        ("Static Files", test_static_files),
        ("Templates", test_templates),
        ("Template Rendering", test_template_rendering),
        ("Server Startup", test_server_startup)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<20} : {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Web UI is ready to use.")
        print("\nTo start the server:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nThen visit: http://localhost:8000")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please fix the issues before running the Web UI.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

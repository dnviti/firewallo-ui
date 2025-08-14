#!/usr/bin/env python3
"""
Test runner for WireGuard Plugin.
Runs all tests and generates comprehensive reports.
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json

# Add paths for testing
plugin_dir = Path(__file__).parent.parent
app_dir = plugin_dir.parent.parent.parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plugin_dir))


class TestRunner:
    """Test runner for WireGuard plugin tests."""

    def __init__(self, verbose: bool = False, coverage: bool = False):
        """Initialize test runner.

        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting
        """
        self.verbose = verbose
        self.coverage = coverage
        self.tests_dir = Path(__file__).parent
        self.plugin_dir = self.tests_dir.parent
        self.results = {}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test modules and return results."""
        print("🧪 Running WireGuard Plugin Test Suite")
        print("=" * 60)

        test_modules = [
            "test_plugin.py",
            "test_integration.py",
            "test_api.py",
            "test_services.py"
        ]

        total_start_time = time.time()
        overall_success = True

        for module in test_modules:
            print(f"\n📋 Running {module}...")
            print("-" * 40)

            success, details = self._run_test_module(module)
            self.results[module] = {
                "success": success,
                "details": details
            }

            if not success:
                overall_success = False

        total_time = time.time() - total_start_time

        # Print summary
        self._print_summary(overall_success, total_time)

        # Generate reports if requested
        if self.coverage:
            self._generate_coverage_report()

        return {
            "success": overall_success,
            "total_time": total_time,
            "results": self.results
        }

    def _run_test_module(self, module: str) -> tuple[bool, Dict[str, Any]]:
        """Run a single test module.

        Args:
            module: Test module filename

        Returns:
            Tuple of (success, details)
        """
        module_path = self.tests_dir / module

        if not module_path.exists():
            print(f"❌ Test module {module} not found")
            return False, {"error": "Module not found"}

        start_time = time.time()

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", str(module_path)]

        if self.verbose:
            cmd.extend(["-v", "-s"])
        else:
            cmd.append("-q")

        if self.coverage:
            cmd.extend([
                "--cov=plugin",
                "--cov=services",
                "--cov-report=term-missing"
            ])

        # Add JSON report for parsing if available
        try:
            import pytest_json_report
            json_report = self.tests_dir / f"{module}.json"
            cmd.extend(["--json-report", f"--json-report-file={json_report}"])
        except ImportError:
            json_report = None

        try:
            # Run tests
            result = subprocess.run(
                cmd,
                cwd=self.tests_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time

            # Parse results
            success = result.returncode == 0

            details = {
                "duration": duration,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            # Try to parse JSON report if available
            if json_report and json_report.exists():
                try:
                    with open(json_report) as f:
                        json_data = json.load(f)
                        details["json_report"] = json_data
                except Exception:
                    pass

            # Print results
            if success:
                print(f"✅ {module} passed ({duration:.2f}s)")
                if self.verbose and result.stdout:
                    print(result.stdout)
            else:
                print(f"❌ {module} failed ({duration:.2f}s)")
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)

            return success, details

        except subprocess.TimeoutExpired:
            print(f"⏰ {module} timed out after 5 minutes")
            return False, {"error": "Timeout", "duration": 300}

        except Exception as e:
            print(f"💥 {module} crashed: {e}")
            return False, {"error": str(e), "duration": 0}

    def _print_summary(self, overall_success: bool, total_time: float):
        """Print test summary.

        Args:
            overall_success: Whether all tests passed
            total_time: Total execution time
        """
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total test modules: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Total time: {total_time:.2f}s")

        print("\nModule Results:")
        for module, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result["details"].get("duration", 0)
            print(f"  {module:<20} {status} ({duration:.2f}s)")

        if overall_success:
            print("\n🎉 All tests passed! WireGuard plugin is ready for production.")
        else:
            print(f"\n❌ {failed_tests} test module(s) failed. Review the errors above.")

        print("\n" + "=" * 60)

    def _generate_coverage_report(self):
        """Generate coverage report."""
        print("\n📈 Generating coverage report...")

        try:
            # Generate HTML coverage report
            subprocess.run([
                sys.executable, "-m", "coverage", "html",
                "--directory", str(self.tests_dir / "coverage_html")
            ], check=True)

            print("✅ Coverage report generated in tests/coverage_html/")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate coverage report: {e}")

    def run_specific_test(self, test_file: str, test_function: str = None) -> bool:
        """Run a specific test file or function.

        Args:
            test_file: Test file to run
            test_function: Optional specific test function

        Returns:
            Whether test passed
        """
        print(f"🧪 Running specific test: {test_file}")
        if test_function:
            print(f"   Function: {test_function}")
        print("-" * 40)

        cmd = [sys.executable, "-m", "pytest"]

        if test_function:
            cmd.append(f"{test_file}::{test_function}")
        else:
            cmd.append(test_file)

        if self.verbose:
            cmd.extend(["-v", "-s"])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.tests_dir,
                timeout=120
            )

            success = result.returncode == 0

            if success:
                print("✅ Test passed")
            else:
                print("❌ Test failed")

            return success

        except Exception as e:
            print(f"💥 Test crashed: {e}")
            return False


def check_dependencies():
    """Check if all required dependencies are available."""
    print("🔍 Checking test dependencies...")

    required_packages = [
        "pytest",
        "pytest-asyncio"
    ]

    optional_packages = [
        "coverage"
    ]

    missing_required = []
    missing_optional = []

    # Check required packages
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing - required)")
            missing_required.append(package)

    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"⚠️  {package} (missing - optional)")
            missing_optional.append(package)

    if missing_required:
        print(f"\n📦 Install required packages:")
        print(f"pip install {' '.join(missing_required)}")
        return False

    if missing_optional:
        print(f"\n📦 Optional packages (for coverage reports):")
        print(f"pip install {' '.join(missing_optional)}")

    print("✅ All required dependencies available")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run WebUI Plugin tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py -v                 # Run with verbose output
  python run_tests.py --coverage         # Run with coverage report
  python run_tests.py --test test_plugin.py  # Run specific test file
  python run_tests.py --check-deps       # Check dependencies only
        """
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "--test",
        help="Run specific test file"
    )

    parser.add_argument(
        "--function",
        help="Run specific test function (requires --test)"
    )

    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies only"
    )

    parser.add_argument(
        "--json-output",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Check dependencies
    if args.check_deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)

    if not check_dependencies():
        sys.exit(1)

    # Create test runner
    runner = TestRunner(verbose=args.verbose, coverage=args.coverage)

    # Run tests
    if args.test:
        # Run specific test
        success = runner.run_specific_test(args.test, args.function)
        results = {"success": success}
    else:
        # Run all tests
        results = runner.run_all_tests()

    # Save JSON output if requested
    if args.json_output:
        try:
            with open(args.json_output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to {args.json_output}")
        except Exception as e:
            print(f"❌ Failed to save JSON output: {e}")

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()

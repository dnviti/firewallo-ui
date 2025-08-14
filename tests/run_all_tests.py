#!/usr/bin/env python3
"""
Main test runner for Firewallo UI project.

This script runs all tests across the entire project including:
- Main application tests
- Plugin system tests
- Individual plugin tests

Usage:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py --coverage         # Run with coverage
    python tests/run_all_tests.py --plugins-only     # Run only plugin tests
    python tests/run_all_tests.py --main-only        # Run only main app tests
    python tests/run_all_tests.py --parallel         # Run tests in parallel
    python tests/run_all_tests.py --integration      # Run integration tests only
"""

import sys
import os
import subprocess
import time
import argparse
import json
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional
import multiprocessing

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ProjectTestRunner:
    """Main test runner for the entire Firewallo UI project."""

    def __init__(self,
                 verbose: bool = False,
                 coverage: bool = False,
                 parallel: bool = False,
                 integration_only: bool = False):
        """Initialize the test runner.

        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            parallel: Run tests in parallel
            integration_only: Run only integration tests
        """
        self.verbose = verbose
        self.coverage = coverage
        self.parallel = parallel
        self.integration_only = integration_only
        self.project_root = project_root
        self.results = {}
        self.start_time = time.time()

    def discover_test_modules(self) -> Dict[str, List[Path]]:
        """Discover all test modules in the project.

        Returns:
            Dictionary mapping test categories to lists of test paths
        """
        test_modules = {
            "main_app": [],
            "plugins_system": [],
            "plugins_individual": []
        }

        # Main application tests
        main_tests_dir = self.project_root / "tests"
        if main_tests_dir.exists():
            for test_file in main_tests_dir.rglob("test_*.py"):
                test_modules["main_app"].append(test_file)

        # Plugin system tests
        plugin_system_tests = self.project_root / "tests" / "test_plugins_system"
        if plugin_system_tests.exists():
            for test_file in plugin_system_tests.glob("test_*.py"):
                test_modules["plugins_system"].append(test_file)

        # Individual plugin tests
        plugins_dir = self.project_root / "app" / "plugins"
        if plugins_dir.exists():
            for plugin_tests_dir in plugins_dir.rglob("tests"):
                if plugin_tests_dir.is_dir():
                    for test_file in plugin_tests_dir.glob("test_*.py"):
                        test_modules["plugins_individual"].append(test_file)

        return test_modules

    def run_test_category(self, category: str, test_files: List[Path]) -> Dict[str, Any]:
        """Run tests for a specific category.

        Args:
            category: Test category name
            test_files: List of test files to run

        Returns:
            Dictionary with test results
        """
        if not test_files:
            return {
                "category": category,
                "success": True,
                "duration": 0,
                "tests_run": 0,
                "message": "No tests found"
            }

        print(f"\n🧪 Running {category} tests...")
        print("=" * 60)

        start_time = time.time()
        total_tests = 0
        failed_tests = 0
        test_results = []

        for test_file in test_files:
            if self.verbose:
                print(f"  Running {test_file.relative_to(self.project_root)}")

            result = self._run_single_test_file(test_file)
            test_results.append(result)
            total_tests += result.get("tests_run", 0)
            if not result.get("success", False):
                failed_tests += 1

        duration = time.time() - start_time
        success = failed_tests == 0

        if success:
            print(f"✅ {category} tests passed ({duration:.2f}s)")
        else:
            print(f"❌ {category} tests failed: {failed_tests}/{len(test_files)} files failed ({duration:.2f}s)")

        return {
            "category": category,
            "success": success,
            "duration": duration,
            "tests_run": total_tests,
            "failed_files": failed_tests,
            "total_files": len(test_files),
            "file_results": test_results
        }

    def _run_single_test_file(self, test_file: Path) -> Dict[str, Any]:
        """Run a single test file.

        Args:
            test_file: Path to the test file

        Returns:
            Test result dictionary
        """
        start_time = time.time()

        # Determine working directory
        if "plugins" in str(test_file) and "tests" in test_file.parts:
            # For plugin tests, run from the plugin's tests directory
            work_dir = test_file.parent
        else:
            # For main app tests, run from project root
            work_dir = self.project_root

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", str(test_file)]

        if self.verbose:
            cmd.extend(["-v", "-s"])
        else:
            cmd.append("-q")

        if self.coverage and "main_app" in str(test_file):
            cmd.extend([
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-append"
            ])

        if self.integration_only:
            cmd.extend(["-m", "integration"])

        # Add JSON report for detailed results
        json_report_file = work_dir / f"test_results_{test_file.stem}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report_file}"])

        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per file
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Parse JSON report if available
            test_count = 0
            if json_report_file.exists():
                try:
                    with open(json_report_file) as f:
                        json_data = json.load(f)
                        test_count = json_data.get("summary", {}).get("total", 0)
                    json_report_file.unlink()  # Clean up
                except Exception:
                    pass

            return {
                "file": str(test_file.relative_to(self.project_root)),
                "success": success,
                "duration": duration,
                "tests_run": test_count,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "file": str(test_file.relative_to(self.project_root)),
                "success": False,
                "duration": 300,
                "tests_run": 0,
                "error": "Timeout after 5 minutes"
            }

        except Exception as e:
            return {
                "file": str(test_file.relative_to(self.project_root)),
                "success": False,
                "duration": 0,
                "tests_run": 0,
                "error": str(e)
            }

    def run_tests_parallel(self, test_modules: Dict[str, List[Path]]) -> Dict[str, Any]:
        """Run tests in parallel.

        Args:
            test_modules: Dictionary of test modules by category

        Returns:
            Combined test results
        """
        print("🚀 Running tests in parallel...")

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=min(multiprocessing.cpu_count(), 4)
        ) as executor:
            futures = {}

            for category, test_files in test_modules.items():
                if test_files:  # Only submit non-empty categories
                    future = executor.submit(self.run_test_category, category, test_files)
                    futures[future] = category

            results = {}
            for future in concurrent.futures.as_completed(futures):
                category = futures[future]
                try:
                    results[category] = future.result()
                except Exception as e:
                    results[category] = {
                        "category": category,
                        "success": False,
                        "duration": 0,
                        "error": str(e)
                    }

        return results

    def run_tests_sequential(self, test_modules: Dict[str, List[Path]]) -> Dict[str, Any]:
        """Run tests sequentially.

        Args:
            test_modules: Dictionary of test modules by category

        Returns:
            Combined test results
        """
        results = {}

        for category, test_files in test_modules.items():
            if test_files:  # Only run non-empty categories
                results[category] = self.run_test_category(category, test_files)

        return results

    def run_all_tests(self,
                     main_only: bool = False,
                     plugins_only: bool = False) -> Dict[str, Any]:
        """Run all tests in the project.

        Args:
            main_only: Run only main application tests
            plugins_only: Run only plugin tests

        Returns:
            Complete test results
        """
        print("🧪 Firewallo UI - Complete Test Suite")
        print("=" * 60)
        print(f"Coverage: {'Enabled' if self.coverage else 'Disabled'}")
        print(f"Parallel: {'Enabled' if self.parallel else 'Disabled'}")
        print(f"Integration Only: {'Yes' if self.integration_only else 'No'}")
        print("=" * 60)

        # Discover test modules
        test_modules = self.discover_test_modules()

        # Filter based on options
        if main_only:
            test_modules = {
                k: v for k, v in test_modules.items()
                if k in ["main_app", "plugins_system"]
            }
        elif plugins_only:
            test_modules = {
                k: v for k, v in test_modules.items()
                if k in ["plugins_system", "plugins_individual"]
            }

        # Print discovery summary
        total_files = sum(len(files) for files in test_modules.values())
        print(f"Discovered {total_files} test files:")
        for category, files in test_modules.items():
            if files:
                print(f"  - {category}: {len(files)} files")

        if total_files == 0:
            print("❌ No test files found!")
            return {"success": False, "message": "No tests found"}

        # Run tests
        if self.parallel and total_files > 1:
            results = self.run_tests_parallel(test_modules)
        else:
            results = self.run_tests_sequential(test_modules)

        # Calculate overall results
        total_duration = time.time() - self.start_time
        overall_success = all(result.get("success", False) for result in results.values())
        total_test_count = sum(result.get("tests_run", 0) for result in results.values())

        # Print summary
        self._print_final_summary(results, total_duration, overall_success, total_test_count)

        # Generate coverage report if enabled
        if self.coverage and overall_success:
            self._generate_coverage_report()

        return {
            "success": overall_success,
            "duration": total_duration,
            "total_tests": total_test_count,
            "categories": results
        }

    def _print_final_summary(self,
                           results: Dict[str, Any],
                           total_duration: float,
                           overall_success: bool,
                           total_test_count: int):
        """Print final test summary.

        Args:
            results: Test results by category
            total_duration: Total execution time
            overall_success: Whether all tests passed
            total_test_count: Total number of tests run
        """
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)

        # Category results
        for category, result in results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            duration = result.get("duration", 0)
            test_count = result.get("tests_run", 0)
            print(f"{category:<20} {status:<8} {test_count:>4} tests ({duration:.2f}s)")

        print("-" * 60)
        print(f"{'TOTAL':<20} {'✅ PASS' if overall_success else '❌ FAIL':<8} {total_test_count:>4} tests ({total_duration:.2f}s)")

        # Detailed failure information
        if not overall_success:
            print("\n❌ FAILED TESTS:")
            for category, result in results.items():
                if not result.get("success", False):
                    failed_files = result.get("failed_files", 0)
                    total_files = result.get("total_files", 0)
                    print(f"  {category}: {failed_files}/{total_files} files failed")

                    # Show individual file failures if verbose
                    if self.verbose and "file_results" in result:
                        for file_result in result["file_results"]:
                            if not file_result.get("success", False):
                                file_path = file_result["file"]
                                error = file_result.get("error", "Test failed")
                                print(f"    - {file_path}: {error}")

        print("\n" + "=" * 60)

        if overall_success:
            print("🎉 ALL TESTS PASSED! The project is ready for deployment.")
        else:
            print("💥 SOME TESTS FAILED! Please review the errors above.")

        print("=" * 60)

    def _generate_coverage_report(self):
        """Generate coverage report."""
        print("\n📈 Generating coverage report...")

        try:
            # Generate HTML coverage report
            subprocess.run([
                sys.executable, "-m", "coverage", "html",
                "--directory", str(self.project_root / "tests" / "coverage_html")
            ], check=True, cwd=self.project_root)

            print("✅ Coverage report generated in tests/coverage_html/")

            # Generate summary
            result = subprocess.run([
                sys.executable, "-m", "coverage", "report", "--show-missing"
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                print("\n📊 Coverage Summary:")
                print(result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate coverage report: {e}")

    def check_dependencies(self) -> bool:
        """Check if all required test dependencies are available.

        Returns:
            True if all dependencies are available
        """
        print("🔍 Checking test dependencies...")

        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-mock",
            "httpx"
        ]

        optional_packages = [
            "pytest-cov",
            "pytest-html",
            "pytest-json-report",
            "pytest-xdist"
        ]

        missing_required = []
        missing_optional = []

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} (required)")
                missing_required.append(package)

        for package in optional_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                print(f"⚠️  {package} (optional)")
                missing_optional.append(package)

        if missing_required:
            print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
            print(f"Install with: pip install {' '.join(missing_required)}")
            return False

        if missing_optional:
            print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
            print(f"Install with: pip install {' '.join(missing_optional)}")

        print("✅ All required dependencies available")
        return True

    def cleanup_test_artifacts(self):
        """Clean up test artifacts and temporary files."""
        print("🧹 Cleaning up test artifacts...")

        cleanup_patterns = [
            "**/.pytest_cache",
            "**/test_results_*.json",
            "**/__pycache__",
            "**/coverage_html",
            "**/.coverage*"
        ]

        cleaned_count = 0
        for pattern in cleanup_patterns:
            for path in self.project_root.rglob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                        cleaned_count += 1
                    elif path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                        cleaned_count += 1
                except Exception:
                    pass  # Ignore cleanup errors

        if cleaned_count > 0:
            print(f"✅ Cleaned up {cleaned_count} test artifacts")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run all tests for Firewallo UI project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_all_tests.py                    # Run all tests
  python tests/run_all_tests.py -v --coverage      # Verbose with coverage
  python tests/run_all_tests.py --plugins-only     # Only plugin tests
  python tests/run_all_tests.py --main-only        # Only main app tests
  python tests/run_all_tests.py --parallel         # Run in parallel
  python tests/run_all_tests.py --integration      # Integration tests only
  python tests/run_all_tests.py --cleanup          # Clean up artifacts
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
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )

    parser.add_argument(
        "--main-only",
        action="store_true",
        help="Run only main application tests"
    )

    parser.add_argument(
        "--plugins-only",
        action="store_true",
        help="Run only plugin tests"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )

    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test artifacts and exit"
    )

    parser.add_argument(
        "--json-output",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.main_only and args.plugins_only:
        print("❌ Cannot specify both --main-only and --plugins-only")
        sys.exit(1)

    # Create test runner
    runner = ProjectTestRunner(
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
        integration_only=args.integration
    )

    # Handle special commands
    if args.cleanup:
        runner.cleanup_test_artifacts()
        sys.exit(0)

    if args.check_deps:
        success = runner.check_dependencies()
        sys.exit(0 if success else 1)

    # Check dependencies before running tests
    if not runner.check_dependencies():
        sys.exit(1)

    try:
        # Run tests
        results = runner.run_all_tests(
            main_only=args.main_only,
            plugins_only=args.plugins_only
        )

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

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

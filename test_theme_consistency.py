#!/usr/bin/env python3
"""
Theme Consistency Test Utility
This script tests the theme system across all WebUI components and plugins
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class ThemeConsistencyTester:
    """Test theme consistency across all WebUI templates and static files."""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.passed = []

        # Theme variables that should be used instead of hardcoded values
        self.theme_variables = {
            'background-color': [
                '--background-color', '--body-bg', '--surface-color', '--surface-secondary',
                '--card-bg', '--sidebar-bg', '--navbar-bg', '--modal-bg', '--dropdown-bg',
                '--table-bg', '--table-header-bg', '--input-bg'
            ],
            'color': [
                '--text-primary', '--text-secondary', '--text-muted', '--text-inverse',
                '--navbar-text', '--sidebar-link-color', '--table-header-text', '--input-text'
            ],
            'border-color': [
                '--border-color', '--border-light', '--border-dark', '--card-border',
                '--sidebar-border', '--table-border', '--input-border', '--modal-border'
            ]
        }

        # Hardcoded values that should be replaced with variables
        self.hardcoded_patterns = {
            'light_backgrounds': [
                '#ffffff', '#fff', 'white', '#f8f9fa', '#e9ecef', '#dee2e6'
            ],
            'dark_backgrounds': [
                '#343a40', '#495057', '#6c757d', '#212529', '#1a202c', '#2d3748'
            ],
            'text_colors': [
                '#333333', '#333', '#666666', '#666', '#999999', '#999',
                '#000000', '#000', 'black', '#212529'
            ]
        }

    def run_all_tests(self) -> bool:
        """Run all theme consistency tests."""
        print("🎨 Running Theme Consistency Tests...")
        print("=" * 50)

        # Test CSS files
        self.test_css_files()

        # Test HTML templates
        self.test_html_templates()

        # Test JavaScript files
        self.test_js_files()

        # Test theme completeness
        self.test_theme_completeness()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def test_css_files(self):
        """Test CSS files for theme consistency."""
        print("\n📄 Testing CSS Files...")

        css_files = list(self.project_root.glob("**/*.css"))

        for css_file in css_files:
            self.test_single_css_file(css_file)

    def test_single_css_file(self, css_file: Path):
        """Test a single CSS file for theme issues."""
        try:
            content = css_file.read_text(encoding='utf-8')

            # Check for hardcoded colors
            self.check_hardcoded_colors(css_file, content)

            # Check for missing !important declarations
            self.check_missing_important(css_file, content)

            # Check for proper CSS variable usage
            self.check_css_variable_usage(css_file, content)

        except Exception as e:
            self.errors.append(f"Error reading {css_file}: {e}")

    def test_html_templates(self):
        """Test HTML templates for theme consistency."""
        print("\n📄 Testing HTML Templates...")

        html_files = list(self.project_root.glob("**/*.html"))

        for html_file in html_files:
            self.test_single_html_file(html_file)

    def test_single_html_file(self, html_file: Path):
        """Test a single HTML file for theme issues."""
        try:
            content = html_file.read_text(encoding='utf-8')

            # Check for inline styles with hardcoded colors
            self.check_inline_styles(html_file, content)

            # Check for theme toggle presence in base templates
            self.check_theme_toggle(html_file, content)

            # Check for proper CSS includes
            self.check_css_includes(html_file, content)

        except Exception as e:
            self.errors.append(f"Error reading {html_file}: {e}")

    def test_js_files(self):
        """Test JavaScript files for theme consistency."""
        print("\n📄 Testing JavaScript Files...")

        js_files = list(self.project_root.glob("**/*.js"))

        for js_file in js_files:
            self.test_single_js_file(js_file)

    def test_single_js_file(self, js_file: Path):
        """Test a single JavaScript file for theme issues."""
        try:
            content = js_file.read_text(encoding='utf-8')

            # Check for hardcoded style manipulation
            self.check_js_style_manipulation(js_file, content)

            # Check for theme API usage
            self.check_theme_api_usage(js_file, content)

        except Exception as e:
            self.errors.append(f"Error reading {js_file}: {e}")

    def test_theme_completeness(self):
        """Test that all necessary theme files exist and are complete."""
        print("\n🔍 Testing Theme Completeness...")

        required_files = [
            "app/static/css/custom.css",
            "app/static/css/plugin-theme-compat.css",
            "app/static/js/common.js",
            "app/static/js/plugin-theme-init.js",
            "app/static/js/theme-enforcer.js"
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required theme file: {file_path}")
            else:
                self.passed.append(f"Found required file: {file_path}")

    def check_hardcoded_colors(self, file_path: Path, content: str):
        """Check for hardcoded color values in CSS."""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            line_num = i + 1

            # Skip comments and variable definitions
            if line.strip().startswith('/*') or line.strip().startswith('*') or '--' in line:
                continue

            # Check for hardcoded colors
            for category, patterns in self.hardcoded_patterns.items():
                for pattern in patterns:
                    if pattern in line and 'var(' not in line:
                        self.warnings.append(
                            f"{file_path}:{line_num} - Hardcoded {category} color '{pattern}' found. "
                            f"Consider using CSS variable instead."
                        )

    def check_missing_important(self, file_path: Path, content: str):
        """Check for missing !important declarations in plugin override CSS."""
        if 'plugin-theme-compat.css' in str(file_path) or 'custom.css' in str(file_path):
            lines = content.split('\n')

            for i, line in enumerate(lines):
                line_num = i + 1

                # Check for CSS properties that should have !important
                if ('background-color:' in line or 'color:' in line or 'border-color:' in line) and \
                   'var(' in line and '!important' not in line and \
                   not line.strip().startswith('/*'):

                    # Skip if it's a variable definition
                    if '--' in line:
                        continue

                    self.warnings.append(
                        f"{file_path}:{line_num} - CSS property may need !important for plugin override"
                    )

    def check_css_variable_usage(self, file_path: Path, content: str):
        """Check for proper CSS variable usage."""
        if 'var(' in content:
            self.passed.append(f"{file_path} - Uses CSS variables ✓")
        else:
            if 'custom.css' in str(file_path):
                self.warnings.append(f"{file_path} - No CSS variables found")

    def check_inline_styles(self, file_path: Path, content: str):
        """Check for problematic inline styles in HTML."""
        # Look for style attributes with hardcoded colors
        style_pattern = r'style\s*=\s*["\'][^"\']*(?:background-color|color)\s*:\s*(?:#[0-9a-fA-F]+|rgb|white|black)[^"\']*["\']'
        matches = re.finditer(style_pattern, content)

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            self.warnings.append(
                f"{file_path}:{line_num} - Inline style with hardcoded color found: {match.group()}"
            )

    def check_theme_toggle(self, file_path: Path, content: str):
        """Check if base templates have theme toggle implementation."""
        if 'base.html' in str(file_path):
            if 'theme-toggle' in content and 'theme-icon' in content:
                self.passed.append(f"{file_path} - Has theme toggle ✓")
            else:
                self.errors.append(f"{file_path} - Missing theme toggle implementation")

    def check_css_includes(self, file_path: Path, content: str):
        """Check if templates include necessary CSS files."""
        if 'base.html' in str(file_path):
            required_css = ['custom.css']
            if 'plugin' in str(file_path) or 'wireguard' in str(file_path):
                required_css.append('plugin-theme-compat.css')

            for css_file in required_css:
                if css_file in content:
                    self.passed.append(f"{file_path} - Includes {css_file} ✓")
                else:
                    self.errors.append(f"{file_path} - Missing {css_file} include")

    def check_js_style_manipulation(self, file_path: Path, content: str):
        """Check for problematic JavaScript style manipulation."""
        # Look for direct style manipulation that might interfere with themes
        problematic_patterns = [
            r'\.style\.backgroundColor\s*=\s*["\']#[0-9a-fA-F]+["\']',
            r'\.style\.color\s*=\s*["\']#[0-9a-fA-F]+["\']',
            r'\.style\.background\s*=\s*["\']#[0-9a-fA-F]+["\']'
        ]

        for pattern in problematic_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.warnings.append(
                    f"{file_path}:{line_num} - Direct style manipulation found: {match.group()}"
                )

    def check_theme_api_usage(self, file_path: Path, content: str):
        """Check for proper theme API usage in JavaScript."""
        if 'theme.' in content or 'ThemeEnforcer' in content:
            self.passed.append(f"{file_path} - Uses theme API ✓")

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 50)
        print("🎨 THEME CONSISTENCY TEST RESULTS")
        print("=" * 50)

        print(f"\n✅ PASSED: {len(self.passed)}")
        for item in self.passed:
            print(f"  ✓ {item}")

        print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
        for item in self.warnings:
            print(f"  ⚠️  {item}")

        print(f"\n❌ ERRORS: {len(self.errors)}")
        for item in self.errors:
            print(f"  ❌ {item}")

        if len(self.errors) == 0:
            print(f"\n🎉 All tests passed! Theme system is consistent.")
        else:
            print(f"\n💥 {len(self.errors)} errors found. Theme system needs fixes.")

        print(f"\nSUMMARY: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")

    def fix_common_issues(self):
        """Automatically fix common theme issues."""
        print("\n🔧 Attempting to fix common theme issues...")

        # This could be extended to automatically fix some issues
        # For now, just provide guidance

        if self.errors or self.warnings:
            print("\nRECOMMENDED FIXES:")
            print("1. Replace hardcoded colors with CSS variables")
            print("2. Add !important declarations to plugin override styles")
            print("3. Include plugin-theme-compat.css in plugin templates")
            print("4. Use theme API instead of direct style manipulation")
            print("5. Add theme toggle to base templates")


def main():
    """Main function to run theme consistency tests."""
    print("🎨 Firewallo UI Theme Consistency Tester")
    print("Testing theme implementation across all WebUI components...")

    # Get project root
    project_root = None
    if len(sys.argv) > 1:
        project_root = sys.argv[1]

    # Run tests
    tester = ThemeConsistencyTester(project_root)
    success = tester.run_all_tests()

    # Offer to fix issues
    if not success:
        response = input("\nWould you like to see recommended fixes? (y/n): ")
        if response.lower() == 'y':
            tester.fix_common_issues()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

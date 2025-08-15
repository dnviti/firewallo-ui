#!/usr/bin/env python3
"""Script to run Plugin WebUI Framework tests."""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_tests():
    """Run all plugin WebUI tests."""
    import pytest

    # Get the test file path
    test_file = Path(__file__).parent / "test_plugin_webui.py"

    logger.info("=" * 60)
    logger.info("Running Plugin WebUI Framework Tests")
    logger.info("=" * 60)

    # Run tests with verbose output and coverage
    args = [
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes",
        "-x",  # Stop on first failure
        "--asyncio-mode=auto"
    ]

    # Add coverage if available
    try:
        import pytest_cov
        args.extend([
            "--cov=app.plugins.base",
            "--cov=app.plugins.system.webui.services",
            "--cov-report=term-missing"
        ])
    except ImportError:
        logger.info("pytest-cov not installed, skipping coverage")

    # Run the tests
    result = pytest.main(args)

    logger.info("=" * 60)
    if result == 0:
        logger.info("✅ All Plugin WebUI tests passed!")
    else:
        logger.error("❌ Some Plugin WebUI tests failed!")
    logger.info("=" * 60)

    return result


async def test_wireguard_webui():
    """Test WireGuard plugin WebUI specifically."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing WireGuard Plugin WebUI Integration")
    logger.info("=" * 60)

    try:
        # Import WireGuard plugin
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        # Create plugin instance
        plugin = WireGuardPlugin()

        # Check WebUI configuration
        logger.info("\n📋 WireGuard WebUI Configuration:")
        logger.info(f"  - WebUI Enabled: {plugin.webui_enabled}")
        logger.info(f"  - Base Path: {plugin.webui_base_path}")
        logger.info(f"  - Has WebUI Router: {plugin.webui_router is not None}")

        # Check manifest
        if plugin.manifest:
            webui_config = plugin.manifest.get('webui', {})
            if webui_config:
                logger.info(f"  - Menu Title: {webui_config.get('menu_entry', {}).get('title')}")
                logger.info(f"  - Icon: {webui_config.get('menu_entry', {}).get('icon')}")
                logger.info(f"  - Use System Theme: {webui_config.get('routes', {}).get('use_system_theme')}")

        # Test WebUI initialization
        logger.info("\n🔧 Testing WebUI Initialization...")
        if plugin.webui_enabled:
            result = await plugin.initialize_webui()
            if result:
                logger.info("  ✅ WebUI initialized successfully")

                # Check WebUI routes
                if plugin.webui_router:
                    routes = []
                    for route in plugin.webui_router.routes:
                        if hasattr(route, 'path'):
                            routes.append(route.path)

                    if routes:
                        logger.info(f"\n📍 Available WebUI Routes:")
                        for route in routes:
                            logger.info(f"    - {plugin.webui_base_path}{route}")
                else:
                    logger.warning("  ⚠️  No WebUI router found")
            else:
                logger.error("  ❌ WebUI initialization failed")
        else:
            logger.info("  ℹ️  WebUI not enabled for this plugin")

        logger.info("\n✅ WireGuard WebUI test completed")

    except Exception as e:
        logger.error(f"❌ Error testing WireGuard WebUI: {e}")
        import traceback
        traceback.print_exc()


async def test_menu_service():
    """Test MenuService functionality."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing MenuService")
    logger.info("=" * 60)

    try:
        from app.plugins.system.webui.services import MenuService

        # Initialize MenuService
        await MenuService.initialize()
        logger.info("✅ MenuService initialized")

        # Test menu registration
        test_menu = {
            'id': 'test_menu',
            'title': 'Test Menu',
            'icon': 'bi-test',
            'url': '/test',
            'category': 'test',
            'position': 100,
            'permissions': [],
            'badge': None,
            'active': True
        }

        result = await MenuService.register_plugin_menu(test_menu)
        if result:
            logger.info("✅ Test menu registered successfully")

            # Get menu entries
            menus = await MenuService.get_menu_entries()
            logger.info(f"📋 Total menu entries: {len(menus)}")

            # Clean up
            await MenuService.unregister_plugin_menu('test_menu')
            logger.info("✅ Test menu unregistered")
        else:
            logger.warning("⚠️  Failed to register test menu")

    except Exception as e:
        logger.error(f"❌ Error testing MenuService: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test runner."""
    logger.info("🚀 Starting Plugin WebUI Framework Tests\n")

    # Run unit tests
    test_result = await run_tests()

    # Run integration tests
    await test_menu_service()
    await test_wireguard_webui()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Summary")
    logger.info("=" * 60)

    if test_result == 0:
        logger.info("✅ All tests completed successfully!")
        logger.info("\n💡 Next Steps:")
        logger.info("  1. Access the WireGuard WebUI at: http://localhost:8000/plugins/vpn/wireguard")
        logger.info("  2. Check the menu integration in the main WebUI")
        logger.info("  3. Test standalone access when system.webui is disabled")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

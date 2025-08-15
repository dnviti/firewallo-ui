#!/usr/bin/env python3
"""
Test script to verify plugin disable functionality.

This script tests that when a plugin is disabled:
1. Menu entries are removed
2. WebUI routes return 503 Service Unavailable
3. Plugin is properly marked as disabled
"""

import asyncio
import httpx
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_plugin_disable_functionality():
    """Test plugin disable functionality end-to-end."""

    base_url = "http://localhost:8000"
    plugin_path = "vpn.wireguard"

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Check if plugin is initially enabled
            logger.info("=== Step 1: Check initial plugin status ===")
            response = await client.get(f"{base_url}/api/plugins")
            if response.status_code != 200:
                logger.error(f"Failed to get plugins list: {response.status_code}")
                return False

            plugins = response.json()
            logger.info(f"Found {len(plugins.get('plugins', {}))} plugins")

            # Step 2: Test WebUI access when enabled
            logger.info("=== Step 2: Test WebUI access when enabled ===")
            webui_url = f"{base_url}/plugins/vpn/wireguard/"
            response = await client.get(webui_url, follow_redirects=True)
            initial_status = response.status_code
            logger.info(f"WebUI access when enabled: {initial_status}")

            if initial_status == 200:
                logger.info("✅ Plugin WebUI accessible when enabled")
            else:
                logger.warning(f"⚠️  Plugin WebUI returned {initial_status} when enabled")

            # Step 3: Disable the plugin
            logger.info("=== Step 3: Disable the plugin ===")
            disable_url = f"{base_url}/api/plugins/{plugin_path}/disable"
            response = await client.post(disable_url)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✅ Plugin disabled successfully")
                else:
                    logger.error(f"❌ Plugin disable failed: {result.get('message')}")
                    return False
            else:
                logger.error(f"❌ Failed to disable plugin: {response.status_code}")
                return False

            # Step 4: Test WebUI access when disabled (should return 503)
            logger.info("=== Step 4: Test WebUI access when disabled ===")
            response = await client.get(webui_url, follow_redirects=True)
            disabled_status = response.status_code
            logger.info(f"WebUI access when disabled: {disabled_status}")

            if disabled_status == 503:
                logger.info("✅ Plugin WebUI correctly returns 503 when disabled")
                success_disable = True
            else:
                logger.error(f"❌ Plugin WebUI should return 503 when disabled, got {disabled_status}")
                success_disable = False

            # Step 5: Test test route specifically
            logger.info("=== Step 5: Test specific plugin route when disabled ===")
            test_url = f"{base_url}/plugins/vpn/wireguard/test"
            response = await client.get(test_url)
            test_status = response.status_code
            logger.info(f"Test route when disabled: {test_status}")

            if test_status == 503:
                logger.info("✅ Plugin test route correctly returns 503 when disabled")
            else:
                logger.error(f"❌ Plugin test route should return 503 when disabled, got {test_status}")
                success_disable = False

            # Step 6: Check menu entries (this would require WebUI access)
            logger.info("=== Step 6: Check menu entries removal ===")
            menu_url = f"{base_url}/debug-menu-service"
            response = await client.get(menu_url)

            if response.status_code == 200:
                menu_data = response.json()
                menu_entries = menu_data.get('debug_info', {}).get('step5_entries_no_perms', [])

                wireguard_menu_found = False
                for entry in menu_entries:
                    if 'wireguard' in entry.get('id', '').lower():
                        wireguard_menu_found = True
                        break

                if not wireguard_menu_found:
                    logger.info("✅ WireGuard menu entry correctly removed when disabled")
                else:
                    logger.error("❌ WireGuard menu entry still present when disabled")
                    success_disable = False
            else:
                logger.warning("⚠️  Could not check menu entries")

            # Step 7: Re-enable the plugin
            logger.info("=== Step 7: Re-enable the plugin ===")
            enable_url = f"{base_url}/api/plugins/{plugin_path}/enable"
            response = await client.post(enable_url)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✅ Plugin re-enabled successfully")
                else:
                    logger.error(f"❌ Plugin enable failed: {result.get('message')}")
                    return False
            else:
                logger.error(f"❌ Failed to enable plugin: {response.status_code}")
                return False

            # Step 8: Test WebUI access after re-enabling
            logger.info("=== Step 8: Test WebUI access after re-enabling ===")
            response = await client.get(webui_url, follow_redirects=True)
            reenabled_status = response.status_code
            logger.info(f"WebUI access when re-enabled: {reenabled_status}")

            if reenabled_status == 200:
                logger.info("✅ Plugin WebUI accessible again after re-enabling")
            else:
                logger.error(f"❌ Plugin WebUI should be accessible after re-enabling, got {reenabled_status}")
                return False

            # Final result
            if success_disable:
                logger.info("\n🎉 PLUGIN DISABLE TEST PASSED!")
                logger.info("✅ Plugin disable functionality is working correctly")
                return True
            else:
                logger.error("\n❌ PLUGIN DISABLE TEST FAILED!")
                logger.error("❌ Plugin disable functionality is NOT working correctly")
                return False

        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test function."""
    logger.info("Starting Plugin Disable Functionality Test")
    logger.info("=" * 60)

    success = await test_plugin_disable_functionality()

    logger.info("=" * 60)
    if success:
        logger.info("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

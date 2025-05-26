#!/usr/bin/env python3
"""
Test script for iOS Interact MCP Server
Tests the basic functionality without the full MCP protocol
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the server components directly from the file
import importlib.util

spec = importlib.util.spec_from_file_location("server", "ios-interact-server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

SimulatorController = server.SimulatorController
list_apps = server.list_apps
screenshot = server.screenshot


async def test_simulator_controller():
    """Test the SimulatorController directly"""
    print("Testing SimulatorController...")
    controller = SimulatorController()

    # Test listing devices
    print("\n1. Testing device listing:")
    success, output = await controller.run_command_async(["list", "devices", "booted"])
    print(f"Success: {success}")
    print(f"Output: {output[:200]}...")

    return success


async def test_list_apps():
    """Test the list_apps function"""
    print("\n2. Testing list_apps function:")
    try:
        result = await list_apps()
        print(f"Result: {result[:500]}...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


async def test_screenshot():
    """Test the screenshot function"""
    print("\n3. Testing screenshot function:")
    try:
        result = await screenshot(filename="test_screenshot.png")
        print(f"Result: {result}")

        # Check if file was created
        if os.path.exists("test_screenshot.png"):
            print("Screenshot file created successfully")
            os.remove("test_screenshot.png")
            return True
        else:
            print("Screenshot file not found")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("iOS Interact MCP Server Test Suite")
    print("=" * 50)

    results = []

    # Run tests
    results.append(await test_simulator_controller())
    results.append(await test_list_apps())
    results.append(await test_screenshot())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

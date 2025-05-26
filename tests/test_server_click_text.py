#!/usr/bin/env python3
"""Direct test of click_text functionality in the MCP server"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr_controller import SimulatorInteractionController
from xcrun_controller import SimulatorController


async def reset_settings():
    """Reset Settings app"""
    print("Resetting Settings app...")
    await SimulatorController.terminate_app("com.apple.Preferences")
    await asyncio.sleep(1)
    await SimulatorController.launch_app("com.apple.Preferences")
    await asyncio.sleep(2)


async def test_click_text():
    """Test click_text functionality"""
    print("=== Testing click_text from MCP Server ===\n")

    # Test 1: Click on General
    print("Test 1: Clicking on 'General'")
    await reset_settings()

    success, message = await SimulatorInteractionController.click_text("General")
    print(f"Result: {success}")
    print(f"Message: {message}")

    # Wait and reset
    await asyncio.sleep(2)

    # Test 2: Click on Camera
    print("\nTest 2: Clicking on 'Camera'")
    await reset_settings()

    success, message = await SimulatorInteractionController.click_text("Camera")
    print(f"Result: {success}")
    print(f"Message: {message}")

    # Test 3: Non-existent text
    print("\nTest 3: Clicking on non-existent text")
    await reset_settings()

    success, message = await SimulatorInteractionController.click_text(
        "NonExistentText"
    )
    print(f"Result: {success}")
    print(f"Message: {message}")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_click_text())

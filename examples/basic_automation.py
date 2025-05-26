#!/usr/bin/env python3
"""Basic automation example using iOS Interact MCP Server"""

import asyncio
import sys
import os

# Add parent directory to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_interact_mcp.ocr_controller import SimulatorInteractionController  # noqa: E402
from ios_interact_mcp.xcrun_controller import SimulatorController  # noqa: E402


async def main():
    """Demonstrate basic iOS automation capabilities"""
    print("iOS Interact MCP - Basic Automation Example")
    print("==========================================\n")

    # Ensure Settings app is running
    print("Launching Settings app...")
    success, message = await SimulatorController.launch_app("com.apple.Preferences")
    if not success:
        print(f"Failed to launch Settings: {message}")
        return

    await asyncio.sleep(2)  # Wait for app to fully launch

    # Take initial screenshot
    print("\nTaking screenshot of Settings main screen...")
    success, screenshot_path = await SimulatorInteractionController.save_screenshot(
        "settings_main.png", return_path=True
    )
    if success:
        print(f"Screenshot saved to: {screenshot_path}")

    # Click on General
    print("\nClicking on 'General'...")
    success, message = await SimulatorInteractionController.click_text("General")
    if success:
        print(f"Success: {message}")
        await asyncio.sleep(1)
    else:
        print(f"Failed: {message}")
        return

    # Find all text in General settings
    print("\nFinding text elements in General settings...")
    success, text_elements = (
        await SimulatorInteractionController.find_text_in_simulator()
    )
    if success:
        # Parse the text elements from the message
        print("Found text elements:")
        lines = text_elements.split("\n")
        for line in lines[:10]:  # Show first 10 items
            if line.strip():
                print(f"  - {line.strip()}")
        if len(lines) > 10:
            print(f"  ... and {len(lines) - 10} more")

    # Click on About
    print("\nClicking on 'About'...")
    success, message = await SimulatorInteractionController.click_text("About")
    if success:
        print(f"Success: {message}")
        await asyncio.sleep(1)
    else:
        print(f"Failed: {message}")

    # Take screenshot of About screen
    print("\nTaking screenshot of About screen...")
    success, screenshot_path = await SimulatorInteractionController.save_screenshot(
        "settings_about.png", return_path=True
    )
    if success:
        print(f"Screenshot saved to: {screenshot_path}")

    # Press home button
    print("\nPressing home button...")
    success, message = await SimulatorController.press_button("home")
    if success:
        print("Returned to home screen")

    print("\nAutomation example complete!")


if __name__ == "__main__":
    asyncio.run(main())

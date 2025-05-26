#!/usr/bin/env python3
"""Test clicking directly without MCP server"""

import asyncio
from ocr_controller import SimulatorInteractionController, SimulatorWindowManager


async def main():
    print("Testing direct click on 'General' text")
    print("=" * 50)

    # First, make sure we can see the current state
    print("\nChecking current window state...")
    windows = await SimulatorWindowManager.get_simulator_windows()
    if windows:
        window = windows[0]
        print(f"Window: {window['name']}")
        print(f"Position: {window['position']}, Size: {window['size']}")

    # Find text elements to see what's on screen
    print("\nFinding all text elements...")
    result, message = await SimulatorInteractionController.find_text_in_simulator()
    print(f"Result: {result}")
    print(f"Message: {message[:200]}...")  # First 200 chars

    # Try to click on "General"
    print("\nAttempting to click on 'General'...")
    result, message = await SimulatorInteractionController.click_text("General")
    print(f"Result: {result}")
    print(f"Message: {message}")

    # Wait a moment for the click to take effect
    await asyncio.sleep(2)

    # Check what's on screen after the click
    print("\nChecking screen after click...")
    result, message = await SimulatorInteractionController.find_text_in_simulator()
    if result:
        # Look for text that would indicate we're in General settings
        expected_texts = [
            "About",
            "Software Update",
            "iPhone Storage",
            "AirDrop",
            "AirPlay",
        ]
        found_any = False
        for text in expected_texts:
            if text.lower() in message.lower():
                print(f"✓ Found '{text}' - click was successful!")
                found_any = True
                break

        if not found_any:
            print(
                "Click may not have worked - didn't find expected General settings items"
            )
            print(f"Current screen shows: {message[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())

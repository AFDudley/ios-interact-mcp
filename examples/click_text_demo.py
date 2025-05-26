#!/usr/bin/env python3
"""Demonstrate OCR text clicking capabilities"""

import asyncio
import sys
import os

# Add parent directory to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_interact_mcp.ocr_controller import SimulatorInteractionController  # noqa: E402
from ios_interact_mcp.xcrun_controller import SimulatorController  # noqa: E402


async def test_click_accuracy():
    """Test clicking on various UI elements"""
    print("iOS Interact MCP - Click Text Demo")
    print("==================================\n")

    # Launch Settings
    print("Launching Settings app...")
    await SimulatorController.terminate_app("com.apple.Preferences")
    await asyncio.sleep(1)
    await SimulatorController.launch_app("com.apple.Preferences")
    await asyncio.sleep(2)

    # Test clicking on different text elements
    test_targets = [
        ("General", "Navigate to General settings"),
        ("About", "Navigate to About section"),
        ("Name", "Click on device name"),
    ]

    for target_text, description in test_targets:
        print(f"\nTest: {description}")
        print(f"Looking for '{target_text}'...")

        # First, find the text to verify it exists
        success, elements = await SimulatorInteractionController.find_text_in_simulator(
            target_text
        )

        if success and target_text in elements:
            print(f"✓ Found '{target_text}'")

            # Click on it
            success, message = await SimulatorInteractionController.click_text(
                target_text
            )

            if success:
                print(f"✓ Successfully clicked: {message}")
                await asyncio.sleep(1.5)  # Wait for navigation

                # Take a screenshot to verify navigation
                success, path = await SimulatorInteractionController.save_screenshot(
                    f"{target_text.lower()}_screen.png", return_path=True
                )
                if success:
                    print(f"  Screenshot: {path}")
            else:
                print(f"✗ Click failed: {message}")
        else:
            print(f"✗ Text '{target_text}' not found")
            # Go back if we're not on the main screen
            if target_text != "General":
                print("  Attempting to go back...")
                # You could implement a back navigation here

    # Test clicking with occurrence parameter
    print("\n\nTesting occurrence parameter...")
    await SimulatorController.terminate_app("com.apple.Preferences")
    await asyncio.sleep(1)
    await SimulatorController.launch_app("com.apple.Preferences")
    await asyncio.sleep(2)

    # Find all instances of a common word
    success, elements = await SimulatorInteractionController.find_text_in_simulator()
    if success:
        # Count occurrences of common words
        words = {}
        for line in elements.split("\n"):
            word = line.strip()
            if word:
                words[word] = words.get(word, 0) + 1

        # Find a word that appears multiple times
        for word, count in words.items():
            if count > 1:
                print(f"\nFound '{word}' {count} times")

                # Click on the second occurrence
                success, message = await SimulatorInteractionController.click_text(
                    word, occurrence=2
                )

                if success:
                    print(f"✓ Clicked on second occurrence: {message}")
                else:
                    print(f"✗ Failed to click second occurrence: {message}")
                break

    print("\n\nDemo complete!")


async def test_coordinate_clicking():
    """Test coordinate-based clicking"""
    print("\n\nCoordinate Clicking Demo")
    print("========================\n")

    # Take a screenshot to get coordinates
    print("Taking screenshot to analyze coordinates...")
    success, path = await SimulatorInteractionController.save_screenshot(
        "coordinate_reference.png", return_path=True
    )

    if success:
        print(f"Reference screenshot: {path}")

        # Find some text elements with their coordinates
        success, elements = await SimulatorInteractionController.find_text_in_simulator(
            "General"
        )

        if success:
            # The elements string contains coordinate information
            print("\nFound element with coordinates")

            # Example of clicking at specific coordinates
            # (In practice, you'd parse the coordinates from the elements)
            print("\nClicking at screen coordinates (200, 300)...")
            success, message = (
                await SimulatorInteractionController.click_at_coordinates(
                    200, 300, "screen"
                )
            )

            if success:
                print(f"✓ Click successful: {message}")
            else:
                print(f"✗ Click failed: {message}")


async def main():
    """Run all demos"""
    await test_click_accuracy()
    await test_coordinate_clicking()


if __name__ == "__main__":
    asyncio.run(main())

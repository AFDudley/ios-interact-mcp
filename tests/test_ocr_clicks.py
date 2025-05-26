#!/usr/bin/env python3
"""Test OCR-based clicking after coordinate fix"""

import asyncio
from ocr_controller import SimulatorWindowManager, OCRTextFinder, CoordinateTransformer
import subprocess


async def reset_simulator_state():
    """Reset simulator to clean state"""
    print("\nResetting simulator state...")

    # Exit fullscreen
    await SimulatorWindowManager.exit_fullscreen()

    # Terminate Settings app
    print("Terminating Settings app...")
    proc = await asyncio.create_subprocess_exec(
        "xcrun",
        "simctl",
        "terminate",
        "booted",
        "com.apple.Preferences",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    # Wait for app to close
    await asyncio.sleep(1)

    # Launch Settings app
    print("Launching Settings app...")
    proc = await asyncio.create_subprocess_exec(
        "xcrun",
        "simctl",
        "launch",
        "booted",
        "com.apple.Preferences",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    # Wait for app to open
    await asyncio.sleep(2)


async def test_click_text(text_to_click):
    """Test clicking on text using OCR"""
    print(f"\n=== Testing click on '{text_to_click}' ===")

    # Take screenshot
    print("Taking fullscreen screenshot...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        use_fullscreen=True
    )

    # Find text
    print(f"Finding '{text_to_click}' in screenshot...")
    text_elements = OCRTextFinder.find_text_elements(
        screenshot_path, search_text=text_to_click
    )

    if not text_elements:
        print(f"'{text_to_click}' not found!")
        return False

    element = text_elements[0]
    print(f"Found at: ({element['center_x']:.0f}, {element['center_y']:.0f})")

    # Transform to screen coordinates
    screen_x, screen_y = CoordinateTransformer.screenshot_to_screen_coordinates(
        element["center_x"], element["center_y"], is_fullscreen=True
    )
    print(f"Screen coordinates: ({screen_x}, {screen_y})")

    # Click
    print(f"Clicking...")
    script = f"""
    tell application "System Events"
        click at {{{screen_x}, {screen_y}}}
    end tell
    """

    proc = await asyncio.create_subprocess_exec(
        "osascript",
        "-e",
        script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        print(f"✓ Click successful")
    else:
        print(f"✗ Click failed: {stderr.decode()}")

    return proc.returncode == 0


async def main():
    # Setup for first test
    await reset_simulator_state()

    # Test clicking on General
    success1 = await test_click_text("General")

    # Reset for second test
    await reset_simulator_state()

    # Test clicking on Camera
    success2 = await test_click_text("Camera")

    # Final cleanup
    await SimulatorWindowManager.exit_fullscreen()

    print(f"\n=== Results ===")
    print(f"General click: {'✓ Success' if success1 else '✗ Failed'}")
    print(f"Camera click: {'✓ Success' if success2 else '✗ Failed'}")


if __name__ == "__main__":
    asyncio.run(main())

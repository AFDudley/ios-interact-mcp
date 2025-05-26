#!/usr/bin/env python3
"""Test simple clicking without fullscreen"""

import asyncio
from ocr_controller import SimulatorWindowManager, OCRTextFinder, CoordinateTransformer


async def main():
    print("Testing simple click without fullscreen")
    print("=" * 50)

    # Get window info
    windows = await SimulatorWindowManager.get_simulator_windows()
    if not windows:
        print("No simulator windows found")
        return

    window = windows[0]
    print(f"Window: {window['name']}")
    print(f"Position: {window['position']}, Size: {window['size']}")

    # Capture screenshot WITHOUT fullscreen
    print("\nCapturing screenshot (windowed mode)...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        use_fullscreen=False
    )
    print(f"Screenshot saved to: {screenshot_path}")

    # Find text elements
    print("\nFinding text elements...")
    elements = OCRTextFinder.find_text_elements(screenshot_path)

    # Look for General
    for elem in elements:
        if elem["text"] == "General":
            print(f"\nFound 'General' at:")
            print(
                f"  Screenshot coords: ({elem['center_x']:.0f}, {elem['center_y']:.0f})"
            )

            # Transform to screen coordinates
            screen_x, screen_y = CoordinateTransformer.screenshot_to_screen_coordinates(
                elem["center_x"], elem["center_y"], window, is_fullscreen=False
            )
            print(f"  Screen coords: ({screen_x}, {screen_y})")

            # Click
            print(f"\nClicking at screen coordinates ({screen_x}, {screen_y})...")
            success = await SimulatorWindowManager.click_at_screen_coordinates(
                screen_x, screen_y
            )
            print(f"Click result: {success}")
            break
    else:
        print("\n'General' not found. Available texts:")
        for i, elem in enumerate(elements[:10]):
            print(f"{i+1}. '{elem['text']}'")


if __name__ == "__main__":
    asyncio.run(main())

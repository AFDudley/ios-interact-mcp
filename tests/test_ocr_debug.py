#!/usr/bin/env python3
"""Debug OCR coordinate issues"""

import asyncio
from pathlib import Path
from ocr_controller import SimulatorWindowManager, OCRTextFinder, CoordinateTransformer


async def test_ocr_coordinates():
    """Test OCR and coordinate transformation"""

    # Get windows
    windows = await SimulatorWindowManager.get_simulator_windows()
    if not windows:
        print("No simulator windows found")
        return

    window = windows[0]
    print(f"Window: {window['name']}")
    print(f"Position: {window['position']}")
    print(f"Size: {window['size']}")

    # Capture screenshot without fullscreen
    print("\n=== Testing Windowed Mode ===")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        window["name"], use_fullscreen=False
    )
    print(f"Screenshot saved to: {screenshot_path}")

    # Run OCR
    elements = OCRTextFinder.find_text_elements(screenshot_path)
    print(f"\nFound {len(elements)} text elements")

    # Show first few elements with their raw coordinates
    for i, elem in enumerate(elements[:5]):
        print(f"\n{i+1}. '{elem['text']}'")
        print(
            f"   Raw OCR coords: x={elem['x']}, y={elem['y']}, w={elem['width']}, h={elem['height']}"
        )
        print(f"   Center: ({elem['center_x']}, {elem['center_y']})")

        # Transform to screen coordinates
        screen_x, screen_y = CoordinateTransformer.screenshot_to_screen_coordinates(
            elem["center_x"], elem["center_y"], window, is_fullscreen=False
        )
        print(f"   Screen coords: ({screen_x}, {screen_y})")

    # Test with fullscreen
    print("\n\n=== Testing Fullscreen Mode ===")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        window["name"], use_fullscreen=True
    )
    print(f"Screenshot saved to: {screenshot_path}")

    # Run OCR
    elements = OCRTextFinder.find_text_elements(screenshot_path)
    print(f"\nFound {len(elements)} text elements")

    # Show first few elements
    for i, elem in enumerate(elements[:5]):
        print(f"\n{i+1}. '{elem['text']}'")
        print(
            f"   Raw OCR coords: x={elem['x']}, y={elem['y']}, w={elem['width']}, h={elem['height']}"
        )
        print(f"   Center: ({elem['center_x']}, {elem['center_y']})")

        # Transform to screen coordinates (should be same in fullscreen)
        screen_x, screen_y = CoordinateTransformer.screenshot_to_screen_coordinates(
            elem["center_x"], elem["center_y"], is_fullscreen=True
        )
        print(f"   Screen coords: ({screen_x}, {screen_y})")

    # Find "General" specifically
    print("\n\n=== Looking for 'General' ===")
    general_elements = [e for e in elements if e["text"] == "General"]
    for elem in general_elements:
        print(f"Found 'General' at:")
        print(
            f"   Raw OCR coords: x={elem['x']}, y={elem['y']}, w={elem['width']}, h={elem['height']}"
        )
        print(f"   Center: ({elem['center_x']}, {elem['center_y']})")


if __name__ == "__main__":
    asyncio.run(test_ocr_coordinates())

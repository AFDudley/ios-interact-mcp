#!/usr/bin/env python3
"""Debug direct clicking"""

import asyncio
from ocr_controller import (
    SimulatorWindowManager,
    OCRTextFinder,
    CoordinateTransformer,
    SimulatorInteractionController,
)


async def main():
    print("Debugging direct click functionality")
    print("=" * 50)

    # Capture screenshot
    print("\nCapturing screenshot...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        use_fullscreen=True
    )
    print(f"Screenshot saved to: {screenshot_path}")

    # Find all text elements
    print("\nFinding all text elements...")
    elements = OCRTextFinder.find_text_elements(screenshot_path)
    print(f"Found {len(elements)} elements")

    # Look for General specifically
    print("\nLooking for 'General'...")
    general_found = False
    for elem in elements:
        if "general" in elem["text"].lower():
            print(
                f"Found: '{elem['text']}' at ({elem['center_x']:.0f}, {elem['center_y']:.0f})"
            )
            general_found = True

            # Try to click it directly
            print(
                f"\nClicking at coordinates ({elem['center_x']:.0f}, {elem['center_y']:.0f})..."
            )
            success = await SimulatorWindowManager.click_at_screen_coordinates(
                int(elem["center_x"]), int(elem["center_y"])
            )
            print(f"Click result: {success}")
            break

    if not general_found:
        print("'General' not found. Here are all text elements:")
        for i, elem in enumerate(elements[:20]):  # First 20 elements
            print(
                f"{i+1}. '{elem['text']}' at ({elem['center_x']:.0f}, {elem['center_y']:.0f})"
            )

    # Exit fullscreen if we entered it
    print("\nExiting fullscreen...")
    await SimulatorWindowManager.exit_fullscreen()


if __name__ == "__main__":
    asyncio.run(main())

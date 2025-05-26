#!/usr/bin/env python3
"""Test OCR text finding functionality"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, ".")

from ios_interact_server import SimulatorWindowManager, OCRTextFinder


async def test_ocr_text_finding():
    print("Testing OCR Text Finding...")

    # Capture screenshot
    print("\nCapturing screenshot...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot()

    if not screenshot_path:
        print("❌ Failed to capture screenshot")
        return False

    print(f"✅ Screenshot captured: {screenshot_path}")

    # Test OCR on the screenshot
    print("\nRunning OCR...")
    elements = OCRTextFinder.find_text_elements(screenshot_path)

    if not elements:
        print("❌ No text found (this might be okay if the screen is empty)")
        # Clean up
        Path(screenshot_path).unlink()
        return False

    print(f"✅ Found {len(elements)} text elements")

    # Show first few elements
    print("\nFirst 5 text elements:")
    for i, elem in enumerate(elements[:5], 1):
        print(
            f"  {i}. '{elem['text']}' at ({elem['center_x']:.0f}, {elem['center_y']:.0f})"
        )

    # Test search functionality
    if elements:
        search_text = (
            elements[0]["text"].split()[0]
            if " " in elements[0]["text"]
            else elements[0]["text"]
        )
        print(f"\nSearching for: '{search_text}'")

        search_results = OCRTextFinder.find_text_elements(screenshot_path, search_text)
        print(f"✅ Found {len(search_results)} matches")

    # Clean up
    Path(screenshot_path).unlink()
    print("\nCleaned up temporary file")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_ocr_text_finding())
    sys.exit(0 if success else 1)

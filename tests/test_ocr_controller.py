#!/usr/bin/env python3
"""Test OCR controller functionality"""

import asyncio
from ocr_controller import (
    SimulatorWindowManager,
    OCRTextFinder,
    CoordinateTransformer,
    SimulatorInteractionController,
)


async def test_window_detection():
    """Test simulator window detection"""
    print("\n=== Testing Window Detection ===")
    windows = await SimulatorWindowManager.get_simulator_windows()
    print(f"Found {len(windows)} simulator window(s):")
    for window in windows:
        print(f"  - {window}")
    return len(windows) > 0


async def test_fullscreen():
    """Test fullscreen functionality"""
    print("\n=== Testing Fullscreen ===")
    windows = await SimulatorWindowManager.get_simulator_windows()
    if not windows:
        print("No simulator windows found")
        return False

    window_name = windows[0]["name"]
    print(f"Making window '{window_name}' fullscreen...")
    success = await SimulatorWindowManager.make_window_fullscreen(window_name)
    print(f"Fullscreen result: {success}")

    if success:
        print("Waiting 2 seconds...")
        await asyncio.sleep(2)
        print("Exiting fullscreen...")
        exit_success = await SimulatorWindowManager.exit_fullscreen()
        print(f"Exit fullscreen result: {exit_success}")

    return success


async def test_screenshot_capture():
    """Test screenshot capture"""
    print("\n=== Testing Screenshot Capture ===")
    windows = await SimulatorWindowManager.get_simulator_windows()
    if not windows:
        print("No simulator windows found")
        return False

    window = windows[0]
    print(f"Capturing screenshot of '{window['name']}'...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        window["name"]
    )
    print(f"Screenshot saved to: {screenshot_path}")
    return screenshot_path is not None


async def test_ocr_text_finding():
    """Test OCR text finding"""
    print("\n=== Testing OCR Text Finding ===")
    result, message = await SimulatorInteractionController.find_text_in_simulator()
    print(f"Result: {result}")
    print(f"Message: {message}")

    if result:
        print("\nTesting specific text search...")
        result, message = await SimulatorInteractionController.find_text_in_simulator(
            "General"
        )
        print(f"Search for 'General': {result}")
        print(f"Message: {message}")

    return result


async def test_click_text():
    """Test clicking on text"""
    print("\n=== Testing Click Text ===")
    print("Attempting to click on 'General' text...")
    result, message = await SimulatorInteractionController.click_text("General")
    print(f"Result: {result}")
    print(f"Message: {message}")
    return result


async def main():
    """Run all tests"""
    print("Starting OCR Controller Tests")
    print("=" * 50)

    # Check if simulator is running
    if not await test_window_detection():
        print("\nERROR: No simulator windows found. Please start the iOS Simulator.")
        return

    # Run tests
    tests = [
        ("Window Detection", test_window_detection),
        ("Fullscreen", test_fullscreen),
        ("Screenshot Capture", test_screenshot_capture),
        ("OCR Text Finding", test_ocr_text_finding),
        ("Click Text", test_click_text),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())

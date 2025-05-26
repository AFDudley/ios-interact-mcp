#!/usr/bin/env python3
"""Test screenshot capture functionality"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, ".")

from ios_interact_server import SimulatorWindowManager


async def test_screenshot_capture():
    print("Testing Screenshot Capture...")

    # First check windows
    windows = await SimulatorWindowManager.get_simulator_windows()
    if not windows:
        print("❌ No simulator windows found")
        return False

    print(f"✅ Found {len(windows)} window(s)")

    # Test capturing first window
    print("\nCapturing screenshot of first window...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot()

    if not screenshot_path:
        print("❌ Screenshot capture failed")
        return False

    if Path(screenshot_path).exists():
        file_size = Path(screenshot_path).stat().st_size
        print(f"✅ Screenshot saved to: {screenshot_path}")
        print(f"   File size: {file_size:,} bytes")

        # Clean up
        Path(screenshot_path).unlink()
        print("   Cleaned up temporary file")
        return True
    else:
        print("❌ Screenshot file not found")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_screenshot_capture())
    sys.exit(0 if success else 1)

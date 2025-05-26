#!/usr/bin/env python3
"""Test window detection functionality"""

import asyncio
import sys

sys.path.insert(0, ".")

from ios_interact_server import SimulatorWindowManager


async def test_window_detection():
    print("Testing Simulator Window Detection...")
    print("Make sure iOS Simulator is running!")

    windows = await SimulatorWindowManager.get_simulator_windows()

    if not windows:
        print("❌ No simulator windows found")
        print("Please open iOS Simulator and try again")
        return False

    print(f"✅ Found {len(windows)} simulator window(s):")

    for i, window in enumerate(windows, 1):
        print(f"\nWindow {i}:")
        print(f"  Name: {window['name']}")
        print(f"  Position: x={window['position'][0]}, y={window['position'][1]}")
        print(f"  Size: {window['size'][0]}x{window['size'][1]}")
        print(f"  ID: {window['id']}")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_window_detection())
    sys.exit(0 if success else 1)

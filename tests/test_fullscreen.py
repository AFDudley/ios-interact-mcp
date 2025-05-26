#!/usr/bin/env python3
"""Test fullscreen functionality directly"""

import asyncio
from ocr_controller import SimulatorWindowManager


async def test_fullscreen():
    """Test fullscreen toggle"""
    print("Testing fullscreen...")

    # Get windows
    windows = await SimulatorWindowManager.get_simulator_windows()
    if not windows:
        print("No simulator windows found")
        return

    window_name = windows[0]["name"]
    print(f"Found window: {window_name}")

    # Enter fullscreen
    print("Entering fullscreen...")
    result = await SimulatorWindowManager.make_window_fullscreen(window_name)
    print(f"Enter fullscreen result: {result}")

    if result:
        print("Waiting 3 seconds...")
        await asyncio.sleep(3)

        # Exit fullscreen
        print("Exiting fullscreen...")
        exit_result = await SimulatorWindowManager.exit_fullscreen()
        print(f"Exit fullscreen result: {exit_result}")
    else:
        # Check stderr output
        print("Fullscreen failed. Let's check what happened...")


if __name__ == "__main__":
    asyncio.run(test_fullscreen())

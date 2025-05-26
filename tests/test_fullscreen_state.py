#!/usr/bin/env python3
import asyncio
from ocr_controller import SimulatorWindowManager


async def main():
    print("Initial state:")
    windows = await SimulatorWindowManager.get_simulator_windows()
    if windows:
        print(f"  Position: {windows[0]['position']}, Size: {windows[0]['size']}")

    print("\nEntering fullscreen...")
    result = await SimulatorWindowManager.make_window_fullscreen()
    print(f"Result: {result}")

    print("\nWaiting 2 seconds...")
    await asyncio.sleep(2)

    print("\nState while in fullscreen:")
    windows = await SimulatorWindowManager.get_simulator_windows()
    if windows:
        print(f"  Position: {windows[0]['position']}, Size: {windows[0]['size']}")

    print("\nExiting fullscreen...")
    result = await SimulatorWindowManager.exit_fullscreen()
    print(f"Result: {result}")

    print("\nWaiting 2 seconds for exit animation...")
    await asyncio.sleep(2)

    print("\nFinal state:")
    windows = await SimulatorWindowManager.get_simulator_windows()
    if windows:
        print(f"  Position: {windows[0]['position']}, Size: {windows[0]['size']}")


asyncio.run(main())

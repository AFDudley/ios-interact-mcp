#!/usr/bin/env python3
import asyncio
from ocr_controller import SimulatorWindowManager


async def main():
    windows = await SimulatorWindowManager.get_simulator_windows()
    for window in windows:
        print(f"Window: {window['name']}")
        print(f"Position: {window['position']}")
        print(f"Size: {window['size']}")
        print(f"Is this fullscreen? Size is {window['size'][0]}x{window['size'][1]}")


asyncio.run(main())

#!/usr/bin/env python3
"""Exit fullscreen"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_mcp.ocr_controller import SimulatorWindowManager  # noqa: E402


async def main():
    try:
        print("Exiting fullscreen...")
        await SimulatorWindowManager.exit_fullscreen()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

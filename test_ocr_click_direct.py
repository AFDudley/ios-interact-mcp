#!/usr/bin/env python3
"""Test OCR controller click directly to see real errors"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_mcp.ocr_controller import SimulatorInteractionController  # noqa: E402


async def main():
    """Test clicking on second Search using OCR controller"""
    controller = SimulatorInteractionController()

    try:
        print("Attempting to click on second 'Search'...")
        success, message = await controller.click_text("Search", occurrence=2)
        print(f"Success: {success}")
        print(f"Message: {message}")
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

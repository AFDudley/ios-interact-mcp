#!/usr/bin/env python3
"""
Test script to reproduce the fullscreen error.
"""

import asyncio
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_mcp.ocr_controller_functional import ensure_fullscreen  # noqa: E402


async def main():
    """Test the fullscreen functionality."""
    print("Testing fullscreen toggle...")
    try:
        result = await ensure_fullscreen()
        print(f"Success! State changed: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

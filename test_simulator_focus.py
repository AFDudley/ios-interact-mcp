#!/usr/bin/env python3
"""
Test script to ensure Simulator is properly focused before sending keystrokes.
"""

import asyncio
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_mcp.ocr_controller import execute_osascript  # noqa: E402


async def test_simulator_focus():
    """Test focusing Simulator before sending keystroke."""
    print("🎯 Testing Simulator focus and keystroke...")

    # Step 1: Activate Simulator application
    print("\n1. Activating Simulator application...")
    try:
        result = await execute_osascript('tell application "Simulator" to activate')
        print(f"   ✅ Simulator activated: {result.returncode == 0}")
    except Exception as e:
        print(f"   ❌ Failed to activate Simulator: {e}")
        return

    # Step 2: Wait a moment for activation
    print("\n2. Waiting for Simulator to become active...")
    await asyncio.sleep(1.0)

    # Step 3: Send keystroke with different approach
    print("\n3. Sending Control+Command+F keystroke...")
    try:
        # Try direct keystroke without process targeting
        result = await execute_osascript(
            'tell application "System Events" to keystroke "f" using '
            "{control down, command down}"
        )
        print(f"   ✅ Keystroke sent: {result.returncode == 0}")
    except Exception as e:
        print(f"   ❌ Failed to send keystroke: {e}")
        return

    # Step 4: Wait and check menu
    print("\n4. Waiting 2 seconds and checking menu...")
    await asyncio.sleep(2.0)

    try:
        result = await execute_osascript("check_fullscreen_menu.applescript")
        print(
            f"   Menu contains 'Exit Full Screen': "
            f"{'Exit Full Screen' in result.stdout}"
        )
        print(
            f"   Menu contains 'Enter Full Screen': "
            f"{'Enter Full Screen' in result.stdout}"
        )
    except Exception as e:
        print(f"   ❌ Failed to check menu: {e}")


if __name__ == "__main__":
    asyncio.run(test_simulator_focus())

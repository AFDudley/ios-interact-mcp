#!/usr/bin/env python3
"""
Debug script for ensure_fullscreen function.
"""

import asyncio
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_mcp.ocr_controller_functional import execute_osascript  # noqa: E402


async def debug_ensure_fullscreen():
    """Debug version of ensure_fullscreen with detailed output."""
    print("🔍 Debugging fullscreen detection...")

    # Step 1: Check initial menu state
    print("\n1. Checking initial menu state...")
    try:
        result = await execute_osascript("check_fullscreen_menu.applescript")
        print(f"   Raw menu output: '{result.stdout}'")
        print(f"   Raw menu stderr: '{result.stderr}'")
        print(f"   Return code: {result.returncode}")

        is_fullscreen = "Exit Full Screen" in result.stdout
        print(f"   Contains 'Exit Full Screen': {is_fullscreen}")
        print(
            f"   Contains 'Enter Full Screen': {'Enter Full Screen' in result.stdout}"
        )
        print(f"   Parsed as fullscreen: {is_fullscreen}")
    except Exception as e:
        print(f"   Error reading menu: {e}")
        is_fullscreen = False

    if is_fullscreen:
        print("   Already in fullscreen, nothing to do")
        return False

    # Step 2: Execute keyboard shortcut
    print("\n2. Executing keyboard shortcut...")

    try:
        await execute_osascript("send_fullscreen_keystroke.applescript")
        print("   ✅ Keyboard shortcut executed successfully")
    except Exception as e:
        print(f"   ❌ Keyboard shortcut failed: {e}")
        return False

    # Step 3: Wait and check multiple times
    print("\n3. Waiting for fullscreen transition...")
    for delay in [0.5, 1.0, 2.0]:
        print(f"   Waiting {delay} seconds...")
        await asyncio.sleep(delay)

        try:
            result = await execute_osascript("check_fullscreen_menu.applescript")
            new_is_fullscreen = "Exit Full Screen" in result.stdout
            state_str = "Fullscreen" if new_is_fullscreen else "Windowed"
            print(f"   After {delay}s: {state_str}")

            if new_is_fullscreen:
                print(f"   ✅ Fullscreen detected after {delay} seconds!")
                break
        except Exception as e:
            print(f"   Error at {delay}s: {e}")

    print("\n4. Final menu state check...")
    try:
        result = await execute_osascript("check_fullscreen_menu.applescript")
        print(f"   Raw menu output: '{result.stdout}'")
        print(f"   Raw menu stderr: '{result.stderr}'")
        print(f"   Return code: {result.returncode}")

        new_is_fullscreen = "Exit Full Screen" in result.stdout
        print(f"   Contains 'Exit Full Screen': {new_is_fullscreen}")
        print(
            f"   Contains 'Enter Full Screen': {'Enter Full Screen' in result.stdout}"
        )
        print(f"   Parsed as fullscreen: {new_is_fullscreen}")
    except Exception as e:
        print(f"   Error reading menu: {e}")
        new_is_fullscreen = False

    # Step 4: Results
    print("\n📊 Results:")
    print(f"   Initial state: {'Fullscreen' if is_fullscreen else 'Windowed'}")
    print(f"   Final state: {'Fullscreen' if new_is_fullscreen else 'Windowed'}")
    print(f"   State changed: {is_fullscreen != new_is_fullscreen}")
    print("   Expected: True (should be fullscreen)")
    print(f"   Actual: {new_is_fullscreen}")

    if not new_is_fullscreen:
        print("\n❌ Failed to enter fullscreen!")
        print("   Possible causes:")
        print("   - Keyboard shortcut doesn't work")
        print("   - Menu detection script isn't working")
        print("   - Timing issue (need longer delay)")
        print("   - Accessibility permissions not granted")
        return False
    else:
        print("\n✅ Successfully entered fullscreen!")
        return True


if __name__ == "__main__":
    asyncio.run(debug_ensure_fullscreen())

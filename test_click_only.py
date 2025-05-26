#!/usr/bin/env python3
"""
Test just the click functionality.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_mcp.ocr_controller_functional import (  # noqa: E402
    setup_clean_simulator_state,
    open_settings_app,
    find_text_in_simulator,
    click_text_in_simulator,
)


async def test_click_only():
    """Test just the click on General."""
    print("🔧 Setting up clean simulator state...")
    await setup_clean_simulator_state()

    print("📱 Opening Settings app...")
    await open_settings_app()
    await asyncio.sleep(1)

    print("📱 Testing click on General...")

    # Capture state before click
    print("   Capturing state before click...")
    before_state = await find_text_in_simulator()

    # Show where General is found
    print("\n   Looking for 'General' text...")
    general_locations = await find_text_in_simulator("General")
    print(f"   Found 'General': {general_locations}")

    # Try to click on General
    print("\n   Sending click to 'General'...")
    await click_text_in_simulator("General")
    await asyncio.sleep(2)  # Longer wait

    # Capture state after click
    print("   Capturing state after click...")
    after_state = await find_text_in_simulator()

    # Check if state changed
    print(f"\n   Before state: {len(before_state)} characters")
    print(f"   After state: {len(after_state)} characters")

    # Calculate the difference
    char_diff = abs(len(after_state) - len(before_state))
    print(f"   Character difference: {char_diff}")

    # Require at least 50 character difference for real navigation
    # (minor changes like clock updates don't count)
    if char_diff < 50:
        print("   ❌ Screen state didn't change significantly - click failed")
        print("   (Minor changes like clock updates don't count as navigation)")
        return False
    else:
        print("   ✅ Screen state changed significantly - click worked")
        return True


if __name__ == "__main__":
    asyncio.run(test_click_only())

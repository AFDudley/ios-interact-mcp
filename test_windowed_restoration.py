#!/usr/bin/env python3
"""
Test windowed mode restoration functionality.
"""

import asyncio
import tempfile
from ios_interact_mcp.ocr_controller_functional import (
    observe_simulator,
    find_text_in_simulator,
    click_text_in_simulator,
    save_screenshot,
)


async def test_windowed_restoration():
    """Test that simulator returns to windowed mode after operations."""

    print("🧪 Testing windowed mode restoration...")

    # Check initial state
    print("\n1. Checking initial state...")
    initial_state = await observe_simulator()
    print(f"   Initial fullscreen state: {initial_state.is_fullscreen}")

    # Test find_text_in_simulator
    print("\n2. Testing find_text_in_simulator...")
    try:
        result = await find_text_in_simulator("Settings")
        print(f"   Found text result: {len(result.split('\n'))} matches")
    except Exception as e:
        print(f"   Error: {e}")

    # Check state after find_text
    after_find_state = await observe_simulator()
    print(f"   State after find_text: {after_find_state.is_fullscreen}")

    # Test save_screenshot
    print("\n3. Testing save_screenshot...")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        try:
            screenshot_path = await save_screenshot(tmp.name)
            print(f"   Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"   Error: {e}")

    # Check state after screenshot
    after_screenshot_state = await observe_simulator()
    print(f"   State after screenshot: {after_screenshot_state.is_fullscreen}")

    # Test click_text_in_simulator (if we can find clickable text)
    print("\n4. Testing click_text_in_simulator...")
    try:
        await click_text_in_simulator("General")
        print("   Click executed successfully")
    except Exception as e:
        print(f"   Error: {e}")

    # Check final state
    final_state = await observe_simulator()
    print(f"   Final state: {final_state.is_fullscreen}")

    # Summary
    print("\n📊 Summary:")
    print(f"   Initial: {'Fullscreen' if initial_state.is_fullscreen else 'Windowed'}")
    print(
        f"   After find_text: {'Fullscreen' if after_find_state.is_fullscreen else 'Windowed'}"
    )
    print(
        f"   After screenshot: {'Fullscreen' if after_screenshot_state.is_fullscreen else 'Windowed'}"
    )
    print(f"   Final: {'Fullscreen' if final_state.is_fullscreen else 'Windowed'}")

    # Verify restoration
    if initial_state.is_fullscreen == final_state.is_fullscreen:
        print("   ✅ Windowed state properly restored!")
    else:
        print("   ❌ Windowed state NOT restored!")


if __name__ == "__main__":
    asyncio.run(test_windowed_restoration())

"""End-to-end tests for simulator interaction.

WARNING: These tests will control your simulator and mouse.
Only run when you have a simulator open and are ready to see it being controlled.
"""

import pytest
import asyncio
from pathlib import Path
import sys
import subprocess
import re
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import (
    click_text_in_simulator,
    click_at_coordinates,
    find_text_in_simulator,
    save_screenshot,
    observe_simulator,
    setup_clean_simulator_state,
    open_settings_app,
)


@pytest.mark.e2e
class TestSimulatorE2E:
    """End-to-end tests that actually control the simulator."""

    @pytest.mark.asyncio
    async def test_observe_and_screenshot(self):
        """Test observing simulator state and taking screenshot."""
        # Set up clean starting state
        print("\n🔧 Setting up clean simulator state...")
        await setup_clean_simulator_state()

        print("\n🔍 Observing simulator state...")
        observation = await observe_simulator()

        assert observation.windows, "No simulator windows found"
        print(f"✅ Found {len(observation.windows)} simulator window(s)")

        # Take screenshot in current state
        print("\n📸 Taking screenshot...")
        screenshot_path = await save_screenshot("/tmp/e2e_test_screenshot.png")
        assert Path(screenshot_path).exists()
        print(f"✅ Screenshot saved to: {screenshot_path}")

        # Check screenshot size
        file_size = Path(screenshot_path).stat().st_size
        print(f"   File size: {file_size:,} bytes")

        # Load image to check dimensions
        with Image.open(screenshot_path) as img:
            width, height = img.size
            print(f"   Dimensions: {width}x{height}")

        # Get screen dimensions for comparison
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True
        )
        screen_width = None
        screen_height = None
        if "Resolution:" in result.stdout:
            for line in result.stdout.split("\n"):
                if "Resolution:" in line:
                    print(f"   Display: {line.strip()}")
                    # Parse resolution like "Resolution: 3024 x 1964"
                    match = re.search(r"(\d+)\s*x\s*(\d+)", line)
                    if match:
                        screen_width = int(match.group(1))
                        screen_height = int(match.group(2))
                    break

        print("\n   📊 Analysis:")
        window_bounds = (
            observation.active_window.bounds if observation.active_window else "N/A"
        )
        print(f"      Window bounds: {window_bounds}")
        print(f"      Screenshot dimensions: {width}x{height}")
        if screen_width and screen_height:
            print(f"      Screen dimensions: {screen_width}x{screen_height}")

        # Small delay to see the effect
        await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_windowed_mode_operations(self):
        """Test that all operations work correctly in windowed mode."""
        # Set up clean starting state
        print("\n🔧 Setting up clean simulator state...")
        await setup_clean_simulator_state()

        print("\n🔄 Testing operations in windowed mode...")

        # Test save_screenshot
        print("   Testing save_screenshot...")
        screenshot_path = await save_screenshot("/tmp/e2e_windowed_test.png")
        print(f"   ✅ Screenshot saved: {screenshot_path}")

        # Test find_text_in_simulator
        print("   Testing find_text_in_simulator...")
        result = await find_text_in_simulator("Settings")
        first_line = result.split("\n")[0]
        print(f"   ✅ Found text: {first_line}")

        # Test click_text_in_simulator
        print("   Testing click_text_in_simulator...")
        # First open Settings to ensure General is available
        await open_settings_app()
        await asyncio.sleep(1)

        await click_text_in_simulator("General")
        print("   ✅ Click completed")

        print("   ✅ All operations work correctly in windowed mode!")

        await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_find_and_click_text(self):
        """Test finding text and clicking on it."""
        # Set up clean starting state and open Settings
        print("\n🔧 Setting up clean simulator state...")
        await setup_clean_simulator_state()

        print("\n📱 Opening Settings app...")
        await open_settings_app()
        await asyncio.sleep(1)

        print("\n🔍 Finding text in simulator...")

        # First, let's see what text is visible
        visible_text = await find_text_in_simulator()
        print("📝 Visible text:")
        for line in visible_text.split("\n")[:5]:  # Show first 5 items
            print(f"   {line}")

        # Should find General in the Settings app we just opened
        print("\n👆 Attempting to click on 'General'...")
        await click_text_in_simulator("General")
        print("✅ Click command sent to 'General'")
        await asyncio.sleep(1)  # See the effect

    @pytest.mark.asyncio
    async def test_coordinate_clicking(self):
        """Test clicking at specific coordinates."""
        # Set up clean starting state
        print("\n🔧 Setting up clean simulator state...")
        await setup_clean_simulator_state()

        print("\n👆 Testing coordinate-based clicking...")

        # Click in the middle of the screen
        observation = await observe_simulator()
        if observation.active_window:
            bounds = observation.active_window.bounds
            center_x = int(bounds.x + bounds.width / 2)
            center_y = int(bounds.y + bounds.height / 2)

            print(f"   Clicking at screen center: ({center_x}, {center_y})")
            await click_at_coordinates(center_x, center_y, "screen")
            await asyncio.sleep(0.5)

            # Click using device coordinates
            print("   Clicking at device coordinates (195, 400)")
            await click_at_coordinates(195, 400, "device")
            await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_screenshot_in_windowed_mode(self):
        """Test that screenshots work correctly in windowed mode."""
        # Set up clean starting state
        print("\n🔧 Setting up clean simulator state...")
        await setup_clean_simulator_state()

        print("\n📸 Testing screenshot in windowed mode...")

        # Take a screenshot
        print("   Taking screenshot...")
        screenshot_path = await save_screenshot("/tmp/e2e_windowed_screenshot.png")

        # Verify screenshot exists and has reasonable size
        from pathlib import Path

        screenshot_file = Path(screenshot_path)
        assert screenshot_file.exists()
        file_size = screenshot_file.stat().st_size
        print(f"   ✅ Screenshot saved: {screenshot_path}")
        print(f"   File size: {file_size:,} bytes")

        # Load and check dimensions
        with Image.open(screenshot_path) as img:
            width, height = img.size
            print(f"   Dimensions: {width}x{height}")
            assert width > 0 and height > 0
            print("   ✅ Screenshot has valid dimensions")

        await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_settings_navigation(self):
        """Test navigating through Settings app."""
        # Set up clean starting state and open Settings
        print("\n🔧 Setting up clean simulator state...")
        await setup_clean_simulator_state()

        print("\n📱 Opening Settings app...")
        await open_settings_app()
        await asyncio.sleep(1)

        print("\n📱 Testing Settings navigation...")

        # Capture state before click
        print("   Capturing state before click...")
        before_state = await find_text_in_simulator()

        # Try to click on General
        print("   Sending click to 'General'...")
        await click_text_in_simulator("General")
        await asyncio.sleep(1)

        # Capture state after click
        print("   Capturing state after click...")
        after_state = await find_text_in_simulator()

        # Verify state actually changed
        if before_state == after_state:
            raise AssertionError("Screen state didn't change after clicking 'General'")
        else:
            print("   ✅ Screen state changed - click was effective")

        # Show what changed
        print("   Visible text after click:")
        for line in after_state.split("\n")[:10]:  # Show first 10 items
            print(f"      {line}")

        # Look for something that should be visible in the General page
        print("   Looking for 'About'...")
        await click_text_in_simulator("About")
        await asyncio.sleep(1)

        # Go back using coordinates (assuming back button is top-left)
        observation = await observe_simulator()
        if observation.active_window:
            # Click approximately where back button would be
            back_x = int(observation.active_window.bounds.x + 50)
            back_y = int(observation.active_window.bounds.y + 50)
            print(f"   Clicking back button area at ({back_x}, {back_y})")
            await click_at_coordinates(back_x, back_y, "screen")


if __name__ == "__main__":
    print("🚀 iOS Simulator E2E Test Suite")
    print("================================")
    print("⚠️  This will control your simulator!")
    print("Make sure you have a simulator running.\n")

    # Run all e2e tests
    pytest.main(
        [__file__, "-v", "-s", "--run-e2e"]  # Show print statements  # Enable e2e tests
    )

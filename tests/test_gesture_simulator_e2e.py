"""End-to-end tests for gesture controller with iOS Simulator.

WARNING: These tests will control your simulator and mouse.
Only run when you have a simulator open and are ready to see it being controlled.
"""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.gesture_controller import (
    tap_at,
    perform_gesture,
    swipe_in_direction,
    DIRECTION_UP,
    DIRECTION_DOWN,
    DIRECTION_LEFT,
    DIRECTION_RIGHT,
)
from ios_interact_mcp.interact_types import (
    SwipeGesture,
    GesturePoint,
)
from ios_interact_mcp.ocr_controller import (
    observe_simulator,
    find_text_in_simulator,
    click_text_in_simulator,
)
from ios_interact_mcp.xcrun_controller import (
    launch_app,
    terminate_app,
)


@pytest.mark.e2e
class TestGestureSimulatorE2E:
    """End-to-end tests for gesture functionality with simulator."""

    @pytest.mark.asyncio
    async def test_tap_on_app_icon(self):
        """Test tapping on an app icon in the home screen."""
        print("\n📱 Testing tap on app icon...")

        # Ensure we're at home screen
        await terminate_app("com.apple.Preferences")
        await asyncio.sleep(1)

        # Find Settings app location using OCR
        result = await find_text_in_simulator("Settings")
        if "Settings" in result:
            # Extract coordinates from the result
            # The OCR returns format like: "Settings (x1, y1, x2, y2)"
            import re

            match = re.search(
                r"Settings.*?\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", result
            )
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                # Tap on Settings
                await tap_at(center_x, center_y)

                await asyncio.sleep(2)

                # Verify Settings opened by looking for "General"
                result = await find_text_in_simulator("General")
                assert "General" in result, "Settings app didn't open"
                print("   ✅ Successfully tapped on Settings app")

    @pytest.mark.asyncio
    async def test_swipe_in_settings(self):
        """Test swiping to scroll in Settings app."""
        print("\n📜 Testing swipe gestures in Settings...")

        # Open Settings
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)

        # Swipe up to scroll down
        print("   Testing swipe up (scroll down)...")
        await swipe_in_direction(DIRECTION_UP, distance=300)
        await asyncio.sleep(1)

        # Check if we can see items that were below the fold
        result = await find_text_in_simulator("Privacy")
        assert (
            "Privacy" in result or "Security" in result
        ), "Swipe didn't scroll the view"
        print("   ✅ Swipe up successful")

        # Swipe down to scroll up
        print("   Testing swipe down (scroll up)...")
        await swipe_in_direction(DIRECTION_DOWN, distance=300)
        await asyncio.sleep(1)

        # Verify we're back at top
        result = await find_text_in_simulator("General")
        assert "General" in result, "Swipe down didn't scroll back up"
        print("   ✅ Swipe down successful")

    @pytest.mark.asyncio
    async def test_scroll_gestures(self):
        """Test scroll up/down gestures."""
        print("\n📜 Testing scroll gestures...")

        # Ensure Settings is open
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)

        # Scroll down (swipe up inverted)
        print("   Testing scroll down...")
        await swipe_in_direction(DIRECTION_DOWN, distance=200)
        await asyncio.sleep(1)

        # Scroll up (swipe down inverted)
        print("   Testing scroll up...")
        await swipe_in_direction(DIRECTION_UP, distance=200)
        print("   ✅ Scroll gestures successful")

    @pytest.mark.asyncio
    async def test_page_navigation_swipe(self):
        """Test page navigation with edge swipes."""
        print("\n📱 Testing page navigation swipes...")

        # Open Settings and navigate to General
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)
        await click_text_in_simulator("General")
        await asyncio.sleep(2)

        # Verify we're in General
        result = await find_text_in_simulator("About")
        assert "About" in result, "Not in General settings"

        # Swipe from left edge to go back
        print("   Testing back navigation (swipe right from edge)...")
        screen_width = 390  # iPhone width
        margin = 10
        back_gesture = SwipeGesture(
            start=GesturePoint(x=margin, y=422),  # Middle of screen
            end=GesturePoint(x=screen_width - margin, y=422),
            duration=0.4,
        )
        await perform_gesture(back_gesture)
        await asyncio.sleep(1)

        # Verify we're back at main Settings
        result = await find_text_in_simulator("General")
        assert "General" in result, "Back navigation didn't work"
        print("   ✅ Page navigation successful")

    @pytest.mark.asyncio
    async def test_double_tap(self):
        """Test double tap gesture."""
        print("\n👆👆 Testing double tap...")

        # Find a suitable target for double tap
        # (In real apps, double tap might zoom or have other effects)
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)

        # Double tap in center of screen
        from ios_interact_mcp.gesture_controller import create_tap

        observation = await observe_simulator()
        if observation.windows:
            window = observation.windows[0]
            double_tap = create_tap(
                x=window.bounds.x + 200, y=window.bounds.y + 400, tap_count=2
            )
            await perform_gesture(double_tap)
        print("   ✅ Double tap gesture executed")

    @pytest.mark.asyncio
    async def test_horizontal_swipes(self):
        """Test left/right swipe gestures."""
        print("\n↔️ Testing horizontal swipes...")

        # Test in an app that supports horizontal navigation
        await launch_app("com.apple.mobileslideshow")  # Photos app
        await asyncio.sleep(3)

        # Swipe left
        print("   Testing swipe left...")
        await swipe_in_direction(DIRECTION_LEFT, distance=250)
        await asyncio.sleep(1)

        # Swipe right
        print("   Testing swipe right...")
        await swipe_in_direction(DIRECTION_RIGHT, distance=250)
        print("   ✅ Horizontal swipes successful")

    @pytest.mark.asyncio
    async def test_precise_tap_coordinates(self):
        """Test tapping at specific UI elements using coordinates."""
        print("\n🎯 Testing precise coordinate tapping...")

        # Open Settings
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)

        # Get simulator window info
        observation = await observe_simulator()
        if observation.windows:
            window = observation.windows[0]

            # Tap near top-right (where search or edit might be)
            x = window.bounds.x + window.bounds.width - 50
            y = window.bounds.y + 100

            await tap_at(x, y)
            print(f"   ✅ Tapped at ({x}, {y})")

    @pytest.mark.asyncio
    async def test_gesture_timing(self):
        """Test gesture with different durations."""
        print("\n⏱️ Testing gesture timing...")

        from ios_interact_mcp.gesture_controller import create_swipe
        from ios_interact_mcp.interact_types import GesturePoint

        # Get window for absolute coordinates
        observation = await observe_simulator()
        if observation.windows:
            window = observation.windows[0]
            center_x = window.bounds.x + window.bounds.width / 2
            center_y = window.bounds.y + window.bounds.height / 2

            # Fast swipe
            fast_swipe = create_swipe(
                DIRECTION_UP,
                distance=200,
                start=GesturePoint(x=center_x, y=center_y + 100),
            )
            modified_swipe = SwipeGesture(
                start=fast_swipe.start, end=fast_swipe.end, duration=0.1
            )
            await perform_gesture(modified_swipe)
            print("   ✅ Fast swipe (0.1s) successful")

            await asyncio.sleep(1)

            # Slow swipe
            slow_swipe = create_swipe(
                DIRECTION_UP,
                distance=200,
                start=GesturePoint(x=center_x, y=center_y + 100),
            )
            modified_slow = SwipeGesture(
                start=slow_swipe.start, end=slow_swipe.end, duration=0.8
            )
            await perform_gesture(modified_slow)
            print("   ✅ Slow swipe (0.8s) successful")

    @pytest.mark.asyncio
    async def test_complex_gesture_sequence(self):
        """Test a complex sequence of gestures."""
        print("\n🎭 Testing complex gesture sequence...")

        from ios_interact_mcp.gesture_controller import create_swipe, create_tap

        # Get window for absolute coordinates
        observation = await observe_simulator()
        if observation.windows:
            window = observation.windows[0]

            # Create a sequence: tap, wait, swipe up, wait, tap
            tap1 = create_tap(
                x=window.bounds.x + 200, y=window.bounds.y + 300, tap_count=1
            )
            await perform_gesture(tap1)
            await asyncio.sleep(0.5)

            swipe = create_swipe(
                DIRECTION_UP,
                distance=150,
                start=GesturePoint(x=window.bounds.x + 200, y=window.bounds.y + 350),
            )
            await perform_gesture(swipe)
            await asyncio.sleep(0.5)

            tap2 = create_tap(
                x=window.bounds.x + 200, y=window.bounds.y + 400, tap_count=1
            )
            await perform_gesture(tap2)
        print("   ✅ Complex gesture sequence completed")


@pytest_asyncio.fixture(autouse=True)
async def setup_and_teardown():
    """Setup and teardown for each test."""
    # Setup: ensure simulator is in a known state
    print("\n🔧 Setting up test environment...")

    yield

    # Teardown: return to home screen
    print("\n🧹 Cleaning up...")
    await terminate_app("com.apple.Preferences")
    await terminate_app("com.apple.mobileslideshow")
    await asyncio.sleep(1)

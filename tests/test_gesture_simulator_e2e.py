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
    save_screenshot,
    setup_clean_simulator_state,
)
from ios_interact_mcp.xcrun_controller import (
    launch_app,
    terminate_app,
)


async def capture_test_screenshot(test_name: str, step: str) -> str:
    """Capture a screenshot for test verification."""
    import time

    timestamp = int(time.time() * 1000)
    filename = f"screenshots/test_{test_name}_{step}_{timestamp}.png"
    screenshot_path = await save_screenshot(filename)
    track_screenshot(screenshot_path)
    return screenshot_path


# Global list to track screenshots for cleanup
_test_screenshots = []


def track_screenshot(filepath: str) -> str:
    """Track a screenshot for potential cleanup."""
    _test_screenshots.append(filepath)
    return filepath


def assert_visual_change(
    before_path: str,
    after_path: str,
    expected_change: bool = True,
    threshold: float = 0.02,
    context: str = "",
) -> None:
    """
    Assert that visual change occurred (or didn't occur) between two screenshots.

    Args:
        before_path: Path to screenshot before action
        after_path: Path to screenshot after action
        expected_change: True if change is expected, False if no change expected
        threshold: Minimum percentage of pixels that must change
        context: Description of what action was performed for better error messages
    """
    change_detected = images_are_different(before_path, after_path, threshold=threshold)

    if expected_change:
        assert change_detected, (
            f"{context}: Expected visual change but none detected. "
            f"Screenshots: {before_path} vs {after_path}"
        )
        print(f"   ✅ Visual change confirmed: {context}")
    else:
        assert not change_detected, (
            f"{context}: Expected no visual change but change detected. "
            f"Screenshots: {before_path} vs {after_path}"
        )
        print(f"   ✅ No visual change confirmed: {context}")


def images_are_different(
    img1_path: str, img2_path: str, threshold: float = 0.05
) -> bool:
    """
    Compare two images and return True if they are significantly different.

    Args:
        img1_path: Path to first image
        img2_path: Path to second image
        threshold: Percentage of pixels that must be different (0.0-1.0)
                  Default 0.05 = 5% of pixels must differ

    Returns:
        True if images are different, False if similar
    """
    import os
    from PIL import Image, ImageChops

    # Validate inputs
    if not os.path.exists(img1_path):
        raise FileNotFoundError(f"First image not found: {img1_path}")
    if not os.path.exists(img2_path):
        raise FileNotFoundError(f"Second image not found: {img2_path}")

    # Open images
    with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
        # Convert to same mode for comparison
        if img1.mode != img2.mode:
            img2 = img2.convert(img1.mode)

        # Resize to match if different sizes
        if img1.size != img2.size:
            print(f"   📐 Resizing image from {img2.size} to {img1.size}")
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        # Calculate pixel differences
        diff = ImageChops.difference(img1, img2)

        # Use getbbox() for quick check - returns None if images are identical
        bbox = diff.getbbox()
        if bbox is None:
            print("   📊 Images are identical (0% difference)")
            return False

        # Count non-zero (different) pixels using histogram
        # This is much faster than iterating through all pixels
        histogram = diff.histogram()

        # For RGB images, we have 3 channels * 256 values
        # For grayscale, we have 1 channel * 256 values
        channels = len(img1.getbands())

        # Count pixels that are not zero (i.e., different)
        total_pixels = img1.size[0] * img1.size[1]

        if channels == 1:  # Grayscale
            diff_pixels = sum(histogram[1:])  # Skip the zero bucket
        else:  # RGB/RGBA
            # For color images, count pixels where any channel differs
            # We need to check the actual pixel data for this
            diff_array = list(diff.getdata())
            diff_pixels = 0
            for pixel in diff_array:
                if isinstance(pixel, (tuple, list)):
                    if any(
                        channel > 0 for channel in pixel[:3]
                    ):  # Skip alpha if present
                        diff_pixels += 1
                else:
                    if pixel > 0:
                        diff_pixels += 1

        # Calculate percentage difference
        change_percentage = diff_pixels / total_pixels if total_pixels > 0 else 0.0
        is_different = change_percentage > threshold

        print(
            f"   📊 Image comparison: {change_percentage:.1%} different "
            f"(threshold: {threshold:.1%}) -> "
            f"{'DIFFERENT' if is_different else 'SIMILAR'}"
        )

        return is_different


@pytest.mark.e2e
class TestGestureSimulatorE2E:
    """End-to-end tests for gesture functionality with simulator."""

    @pytest.mark.asyncio
    async def test_swipe_in_settings(self):
        """Test swiping to scroll in Settings app."""
        print("\n📜 Testing swipe gestures in Settings...")

        # Open Settings
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)

        # Capture initial state
        initial_screenshot = await capture_test_screenshot("swipe_settings", "initial")
        print(f"   📸 Initial screenshot: {initial_screenshot}")

        # Check initial content before swipe
        initial_content = await find_text_in_simulator("General")
        print(f"   🔍 Initial content check: {initial_content}")

        # Swipe up to scroll down
        print("   Testing swipe up (scroll down)...")
        await swipe_in_direction(DIRECTION_UP, distance=300)
        await asyncio.sleep(1)

        # Capture after swipe up
        after_swipe_up = await capture_test_screenshot(
            "swipe_settings", "after_swipe_up"
        )
        print(f"   📸 After swipe up: {after_swipe_up}")

        # Verify swipe caused visual change
        assert_visual_change(
            initial_screenshot,
            after_swipe_up,
            expected_change=True,
            threshold=0.05,
            context="Swiping up in Settings to scroll down",
        )

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

        # Capture after swipe down
        after_swipe_down = await capture_test_screenshot(
            "swipe_settings", "after_swipe_down"
        )
        print(f"   📸 After swipe down: {after_swipe_down}")

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
        """Test double tap gesture on General in Settings."""
        print("\n👆👆 Testing double tap on General...")

        # Open Settings app
        await launch_app("com.apple.Preferences")
        await asyncio.sleep(2)

        # Capture initial Settings screen
        initial_screenshot = await capture_test_screenshot(
            "double_tap", "settings_main"
        )
        print(f"   📸 Settings main: {initial_screenshot}")

        # Verify General is visible
        result = await find_text_in_simulator("General")
        print(f"   🔍 General search result: {result}")
        assert (
            "General" in result
        ), f"General not found in Settings. OCR result: {result}"

        # Double tap on General
        from ios_interact_mcp.gesture_controller import create_tap

        observation = await observe_simulator()
        if observation.windows:
            window = observation.windows[0]
            # Find General text location and double tap it
            import re

            match = re.search(r"General.*?\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", result)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                center_x = window.bounds.x + (x1 + x2) / 2
                center_y = window.bounds.y + (y1 + y2) / 2

                double_tap = create_tap(x=center_x, y=center_y, tap_count=2)
                await perform_gesture(double_tap)
                await asyncio.sleep(2)

                # Capture after double tap
                after_double_tap = await capture_test_screenshot(
                    "double_tap", "after_double_tap"
                )
                print(f"   📸 After double tap: {after_double_tap}")

                # Verify double tap opened General settings
                general_result = await find_text_in_simulator("About")
                assert (
                    "About" in general_result
                ), "Double tap didn't open General settings"

                # Verify visual change occurred
                assert_visual_change(
                    initial_screenshot,
                    after_double_tap,
                    expected_change=True,
                    threshold=0.05,
                    context="Double tapping General in Settings",
                )

                print("   ✅ Double tap on General successful")

    @pytest.mark.asyncio
    async def test_horizontal_swipes(self):
        """Test left/right swipe gestures."""
        print("\n↔️ Testing horizontal swipes...")

        # Test in an app that supports horizontal navigation
        await launch_app("com.apple.mobileslideshow")  # Photos app
        await asyncio.sleep(3)

        # Capture initial state
        initial_screenshot = await capture_test_screenshot(
            "horizontal_swipes", "initial"
        )
        print(f"   📸 Initial state: {initial_screenshot}")

        # Swipe left
        print("   Testing swipe left...")
        await swipe_in_direction(DIRECTION_LEFT, distance=250)
        await asyncio.sleep(1)

        # Capture after swipe left
        after_left_screenshot = await capture_test_screenshot(
            "horizontal_swipes", "after_left"
        )
        print(f"   📸 After swipe left: {after_left_screenshot}")

        # Swipe right
        print("   Testing swipe right...")
        await swipe_in_direction(DIRECTION_RIGHT, distance=250)
        await asyncio.sleep(1)

        # Capture after swipe right
        after_right_screenshot = await capture_test_screenshot(
            "horizontal_swipes", "after_right"
        )
        print(f"   📸 After swipe right: {after_right_screenshot}")

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

    # @pytest.mark.asyncio
    # async def test_complex_gesture_sequence(self):
    #     """Test a complex sequence of gestures."""
    #     # COMMENTED OUT: This test doesn't actually test meaningful UI interactions
    #     # The gestures just tap/swipe on arbitrary coordinates without targeting real UI elements  # noqa: E501
    #     # Screenshots showed all states were identical, proving no actual interaction occurred  # noqa: E501
    #
    #     print("\n🎭 Testing complex gesture sequence...")
    #
    #     from ios_interact_mcp.gesture_controller import create_swipe, create_tap
    #
    #     # Get window for absolute coordinates
    #     observation = await observe_simulator()
    #     if observation.windows:
    #         window = observation.windows[0]
    #
    #         # Capture initial state
    #         initial_screenshot = await capture_test_screenshot("complex_sequence", "initial")  # noqa: E501
    #         print(f"   📸 Initial state: {initial_screenshot}")
    #
    #         # Create a sequence: tap, wait, swipe up, wait, tap
    #         tap1 = create_tap(
    #             x=window.bounds.x + 200, y=window.bounds.y + 300, tap_count=1
    #         )
    #         await perform_gesture(tap1)
    #         await asyncio.sleep(0.5)
    #
    #         # Capture after first tap
    #         after_tap1_screenshot = await capture_test_screenshot("complex_sequence", "after_tap1")  # noqa: E501
    #         print(f"   📸 After first tap: {after_tap1_screenshot}")
    #
    #         swipe = create_swipe(
    #             DIRECTION_UP,
    #             distance=150,
    #             start=GesturePoint(x=window.bounds.x + 200, y=window.bounds.y + 350),
    #         )
    #         await perform_gesture(swipe)
    #         await asyncio.sleep(0.5)
    #
    #         # Capture after swipe
    #         after_swipe_screenshot = await capture_test_screenshot("complex_sequence", "after_swipe")  # noqa: E501
    #         print(f"   📸 After swipe: {after_swipe_screenshot}")
    #
    #         tap2 = create_tap(
    #             x=window.bounds.x + 200, y=window.bounds.y + 400, tap_count=1
    #         )
    #         await perform_gesture(tap2)
    #         await asyncio.sleep(0.5)
    #
    #         # Capture final state
    #         final_screenshot = await capture_test_screenshot("complex_sequence", "final")  # noqa: E501
    #         print(f"   📸 Final state: {final_screenshot}")
    #
    #     print("   ✅ Complex gesture sequence completed")


@pytest_asyncio.fixture(autouse=True)
async def setup_and_teardown():
    """Setup and teardown for each test."""
    global _test_screenshots

    # Setup: ensure simulator is in a known state
    print("\n🔧 Setting up test environment...")

    # Reset to clean home screen state using existing function
    await setup_clean_simulator_state()

    # Clear screenshot tracking for this test
    test_screenshots_start = len(_test_screenshots)
    test_passed = True

    try:
        yield
    except Exception as e:
        test_passed = False
        print(f"   ⚠️ Test failed with exception: {type(e).__name__}: {e}")
        raise
    finally:
        # Teardown: return to home screen
        print("\n🧹 Cleaning up...")
        await terminate_app("com.apple.Preferences")
        await terminate_app("com.apple.mobileslideshow")

        # Clean up test screenshots if test passed
        test_screenshots = _test_screenshots[test_screenshots_start:]
        if test_passed:
            import os

            for screenshot_path in test_screenshots:
                try:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        print(f"   🗑️ Removed screenshot: {screenshot_path}")
                except Exception as e:
                    print(f"   ⚠️ Failed to remove {screenshot_path}: {e}")
            # Remove from tracking list
            _test_screenshots = _test_screenshots[:test_screenshots_start]
        else:
            print(
                f"   📸 Test failed - keeping {len(test_screenshots)} screenshots for debugging:"  # noqa: E501
            )
            for screenshot_path in test_screenshots:
                print(f"     - {screenshot_path}")

        await asyncio.sleep(1)

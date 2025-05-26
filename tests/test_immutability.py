"""Tests for data type immutability."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.types import (
    Point,
    Rectangle,
    Window,
    TextMatch,
    Screenshot,
    SimulatorObservation,
    ClickAction,
    KeyboardAction,
    ScreenshotAction,
)


class TestImmutability:
    """Test that all data types are properly immutable."""

    def test_point_immutable(self):
        """Test Point immutability."""
        point = Point(x=10, y=20)

        with pytest.raises(AttributeError):
            point.x = 30

        with pytest.raises(AttributeError):
            point.y = 40

    def test_rectangle_immutable(self):
        """Test Rectangle immutability."""
        rect = Rectangle(x=0, y=0, width=100, height=100)

        with pytest.raises(AttributeError):
            rect.x = 10

        with pytest.raises(AttributeError):
            rect.width = 200

    def test_rectangle_center_computed(self):
        """Test Rectangle center is computed property."""
        rect = Rectangle(x=100, y=200, width=50, height=80)
        center1 = rect.center
        center2 = rect.center

        # Should return new Point instances
        assert center1 == center2
        assert center1 is not center2  # Different objects
        assert center1.x == 125
        assert center1.y == 240

    def test_window_immutable(self):
        """Test Window immutability."""
        window = Window(index=1, bounds=Rectangle(0, 0, 390, 844), title="iPhone 14")

        with pytest.raises(AttributeError):
            window.index = 2

        with pytest.raises(AttributeError):
            window.title = "iPhone 15"

        # Nested objects should also be immutable
        with pytest.raises(AttributeError):
            window.bounds.x = 100

    def test_text_match_immutable(self):
        """Test TextMatch immutability."""
        match = TextMatch(
            text="Hello", confidence=0.95, bounds=Rectangle(10, 20, 30, 40)
        )

        with pytest.raises(AttributeError):
            match.text = "World"

        with pytest.raises(AttributeError):
            match.confidence = 0.99

    def test_screenshot_immutable(self):
        """Test Screenshot immutability."""
        screenshot = Screenshot(
            path=Path("/tmp/test.png"),
            bounds=Rectangle(0, 0, 390, 844),
            timestamp=1234567890.0,
        )

        with pytest.raises(AttributeError):
            screenshot.path = Path("/tmp/other.png")

        with pytest.raises(AttributeError):
            screenshot.timestamp = 9999999999.0

    def test_simulator_observation_immutable(self):
        """Test SimulatorObservation immutability."""
        windows = [Window(1, Rectangle(0, 0, 390, 844), "iPhone")]
        obs = SimulatorObservation(
            windows=windows,
            is_fullscreen=False,
            active_window=windows[0],
            timestamp=1234567890.0,
        )

        with pytest.raises(AttributeError):
            obs.is_fullscreen = True

        # List should be immutable at the dataclass level
        with pytest.raises(AttributeError):
            obs.windows = []

        # But the list itself is still mutable (Python limitation)
        # This is a known limitation of frozen dataclasses
        obs.windows.append(Window(2, Rectangle(0, 0, 390, 844), "iPad"))
        assert len(obs.windows) == 2

    def test_click_action_immutable(self):
        """Test ClickAction immutability."""
        action = ClickAction(screen_point=Point(100, 200), description="Click button")

        with pytest.raises(AttributeError):
            action.description = "Different action"

        with pytest.raises(AttributeError):
            action.screen_point = Point(300, 400)

    def test_keyboard_action_immutable(self):
        """Test KeyboardAction immutability."""
        action = KeyboardAction(key_combo="cmd+c", description="Copy")

        with pytest.raises(AttributeError):
            action.key_combo = "cmd+v"

    def test_screenshot_action_immutable(self):
        """Test ScreenshotAction immutability."""
        action = ScreenshotAction(
            window=Window(1, Rectangle(0, 0, 390, 844), "Test"),
            output_path=Path("/tmp/screenshot.png"),
        )

        with pytest.raises(AttributeError):
            action.output_path = Path("/tmp/other.png")

        with pytest.raises(AttributeError):
            action.window = Window(2, Rectangle(0, 0, 390, 844), "Other")

    def test_creating_modified_copies(self):
        """Test the functional way to 'modify' immutable objects."""
        point1 = Point(x=10, y=20)

        # Create a new point with modified x
        point2 = Point(x=30, y=point1.y)

        assert point1.x == 10  # Original unchanged
        assert point2.x == 30  # New point with different x
        assert point2.y == 20  # Same y value

        # Similarly for rectangles
        rect1 = Rectangle(x=0, y=0, width=100, height=100)
        rect2 = Rectangle(x=rect1.x, y=rect1.y, width=200, height=rect1.height)

        assert rect1.width == 100
        assert rect2.width == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

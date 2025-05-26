"""Tests for pure functions in ocr_controller_functional."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import (
    parse_window_data,
    parse_menu_state,
    transform_coordinates,
    select_window,
    calculate_click_point,
    load_applescript,
)
from ios_interact_mcp.types import Point, Rectangle, Window, TextMatch


class TestPureFunctions:
    """Test pure transformation and parsing functions."""

    def test_parse_window_data_single(self):
        """Test parsing single window data."""
        output = "1, 100, 200, 390, 844, iPhone 14 - iOS 17.2"
        windows = parse_window_data(output)

        assert len(windows) == 1
        assert windows[0].index == 1
        assert windows[0].bounds.x == 100
        assert windows[0].bounds.y == 200
        assert windows[0].bounds.width == 390
        assert windows[0].bounds.height == 844
        assert windows[0].title == "iPhone 14 - iOS 17.2"

    def test_parse_window_data_multiple(self):
        """Test parsing multiple windows."""
        output = """1, 0, 0, 390, 844, iPhone 14
2, 400, 0, 390, 844, iPhone 15 Pro"""
        windows = parse_window_data(output)

        assert len(windows) == 2
        assert windows[1].index == 2
        assert windows[1].bounds.x == 400

    def test_parse_window_data_empty(self):
        """Test parsing empty window data."""
        windows = parse_window_data("")
        assert len(windows) == 0

    def test_parse_menu_state_fullscreen(self):
        """Test parsing menu state for fullscreen."""
        # "Exit Full Screen" in menu means we ARE in fullscreen
        output = """Exit Full Screen
Window"""
        assert parse_menu_state(output) is True

        # "Enter Full Screen" in menu means we are NOT in fullscreen
        output = """Enter Full Screen
Window"""
        assert parse_menu_state(output) is False

    def test_transform_coordinates(self):
        """Test coordinate transformation between rectangles."""
        point = Point(x=10, y=20)
        from_bounds = Rectangle(x=0, y=0, width=100, height=100)
        to_bounds = Rectangle(x=1000, y=500, width=200, height=400)

        result = transform_coordinates(point, from_bounds, to_bounds)

        # 10% of 200 = 20, plus 1000 = 1020
        assert result.x == 1020
        # 20% of 400 = 80, plus 500 = 580
        assert result.y == 580

    def test_transform_coordinates_identity(self):
        """Test transform with identical rectangles."""
        point = Point(x=50, y=75)
        bounds = Rectangle(x=0, y=0, width=100, height=100)

        result = transform_coordinates(point, bounds, bounds)
        assert result.x == point.x
        assert result.y == point.y

    def test_select_window_by_name(self):
        """Test window selection by device name."""
        windows = [
            Window(1, Rectangle(0, 0, 390, 844), "iPhone 14"),
            Window(2, Rectangle(400, 0, 390, 844), "iPhone 15 Pro"),
        ]

        selected = select_window(windows, "iPhone 15")
        assert selected is not None
        assert selected.index == 2

    def test_select_window_default(self):
        """Test default window selection."""
        windows = [
            Window(1, Rectangle(0, 0, 390, 844), "iPhone 14"),
            Window(2, Rectangle(400, 0, 390, 844), "iPhone 15 Pro"),
        ]

        selected = select_window(windows, None)
        assert selected is not None
        assert selected.index == 1

    def test_select_window_empty_list(self):
        """Test window selection with empty list."""
        selected = select_window([], "iPhone")
        assert selected is None

    def test_calculate_click_point(self):
        """Test click point calculation from text match."""
        text_match = TextMatch(
            text="Hello",
            confidence=0.95,
            bounds=Rectangle(x=100, y=150, width=50, height=30),
        )
        screenshot_bounds = Rectangle(x=0, y=0, width=390, height=844)
        window_bounds = Rectangle(x=1000, y=100, width=390, height=844)

        click_point = calculate_click_point(
            text_match, screenshot_bounds, window_bounds, 844  # image height
        )

        # Should transform center point from screenshot to screen coordinates
        assert isinstance(click_point, Point)
        assert click_point.x > 1000  # Should be within window bounds

    def test_load_applescript(self):
        """Test loading AppleScript from file."""
        # This will work if applescripts directory exists
        try:
            script = load_applescript("enumerate_windows.applescript")
            assert 'tell application "System Events"' in script
        except FileNotFoundError:
            pytest.skip("AppleScript files not found")

    def test_load_applescript_missing(self):
        """Test loading non-existent AppleScript."""
        with pytest.raises(FileNotFoundError):
            load_applescript("nonexistent.applescript")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

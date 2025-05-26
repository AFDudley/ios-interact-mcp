"""Tests for OCR functions in ocr_controller_functional."""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import (
    perform_ocr,
    parse_ocr_bounds,
    vision_to_pil_coordinates,
)
from ios_interact_mcp.types import Rectangle, Point, TextMatch


class TestOCRFunctions:
    """Test OCR-related pure functions."""

    @pytest.fixture
    def test_images_dir(self):
        """Get the test images directory."""
        return Path(__file__).parent

    def test_perform_ocr_hello_world(self, test_images_dir):
        """Test OCR on simple hello world image."""
        image_path = test_images_dir / "test_hello_world.png"
        matches = perform_ocr(image_path)

        assert len(matches) > 0
        assert any("Hello" in match.text for match in matches)
        assert all(match.confidence > 0 for match in matches)

    def test_perform_ocr_with_search(self, test_images_dir):
        """Test OCR with search text."""
        image_path = test_images_dir / "test_hello_world.png"
        matches = perform_ocr(image_path, "Hello")

        assert len(matches) > 0
        assert all("hello" in match.text.lower() for match in matches)

    def test_perform_ocr_no_match(self, test_images_dir):
        """Test OCR when search text doesn't match."""
        image_path = test_images_dir / "test_hello_world.png"
        matches = perform_ocr(image_path, "Goodbye")

        assert len(matches) == 0

    def test_parse_ocr_bounds(self):
        """Test parsing of OCR bounds string."""
        bounds_str = "{{100, 200}, {300, 400}}"
        rect = parse_ocr_bounds(bounds_str)

        assert rect.x == 100
        assert rect.y == 200
        assert rect.width == 300
        assert rect.height == 400

    def test_parse_ocr_bounds_invalid(self):
        """Test parsing of invalid bounds string."""
        with pytest.raises(ValueError):
            parse_ocr_bounds("invalid bounds")

    def test_vision_to_pil_coordinates(self):
        """Test coordinate conversion from Vision to PIL."""
        vision_point = Point(100, 150)
        pil_point = vision_to_pil_coordinates(vision_point, 500)

        assert pil_point.x == 100
        assert pil_point.y == 350  # 500 - 150

    def test_rectangle_center(self):
        """Test Rectangle center property."""
        rect = Rectangle(x=100, y=200, width=50, height=80)
        center = rect.center

        assert center.x == 125  # 100 + 50/2
        assert center.y == 240  # 200 + 80/2

    def test_simulator_settings_image(self, test_images_dir):
        """Test OCR on simulator-like settings image."""
        image_path = test_images_dir / "test_simulator_settings.png"

        # Test finding "General"
        matches = perform_ocr(image_path, "General")
        assert len(matches) > 0
        assert any("General" in match.text for match in matches)

        # Test finding all text
        all_matches = perform_ocr(image_path)
        text_found = [match.text for match in all_matches]

        # Should find multiple settings items
        assert len(all_matches) > 5
        assert any("Settings" in text for text in text_found)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

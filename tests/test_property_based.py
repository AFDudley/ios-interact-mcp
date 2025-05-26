"""Property-based tests for ocr_controller_functional."""

import pytest
from hypothesis import given, strategies as st, assume
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import (
    transform_coordinates,
    vision_to_pil_coordinates,
    parse_window_data,
)
from ios_interact_mcp.types import Point, Rectangle


class TestPropertyBased:
    """Property-based tests to verify mathematical properties."""

    @given(
        x=st.floats(min_value=0, max_value=10000, allow_nan=False),
        y=st.floats(min_value=0, max_value=10000, allow_nan=False),
        width=st.floats(min_value=1, max_value=10000, allow_nan=False),
        height=st.floats(min_value=1, max_value=10000, allow_nan=False),
    )
    def test_transform_identity(self, x, y, width, height):
        """Test that transforming within same rectangle is identity."""
        rect = Rectangle(x=x, y=y, width=width, height=height)
        point = Point(x=x + width / 2, y=y + height / 2)  # Center point

        result = transform_coordinates(point, rect, rect)

        # Should be approximately the same (floating point precision)
        assert abs(result.x - point.x) < 0.0001
        assert abs(result.y - point.y) < 0.0001

    @given(
        point_x=st.floats(min_value=0, max_value=1, allow_nan=False),
        point_y=st.floats(min_value=0, max_value=1, allow_nan=False),
        from_width=st.floats(min_value=1, max_value=1000, allow_nan=False),
        from_height=st.floats(min_value=1, max_value=1000, allow_nan=False),
        to_width=st.floats(min_value=1, max_value=1000, allow_nan=False),
        to_height=st.floats(min_value=1, max_value=1000, allow_nan=False),
    )
    def test_transform_preserves_relative_position(
        self, point_x, point_y, from_width, from_height, to_width, to_height
    ):
        """Test that relative position is preserved in transformation."""
        # Use normalized coordinates for the point
        from_rect = Rectangle(x=0, y=0, width=from_width, height=from_height)
        to_rect = Rectangle(x=0, y=0, width=to_width, height=to_height)

        # Point at relative position
        point = Point(x=point_x * from_width, y=point_y * from_height)

        result = transform_coordinates(point, from_rect, to_rect)

        # Calculate relative position in result
        rel_x = result.x / to_width
        rel_y = result.y / to_height

        # Should preserve relative position
        assert abs(rel_x - point_x) < 0.0001
        assert abs(rel_y - point_y) < 0.0001

    @given(
        x=st.floats(min_value=0, max_value=10000, allow_nan=False),
        y=st.floats(min_value=0, max_value=10000, allow_nan=False),
        height=st.floats(min_value=1, max_value=10000, allow_nan=False),
    )
    def test_vision_to_pil_inverse(self, x, y, height):
        """Test that vision to PIL conversion can be inverted."""
        vision_point = Point(x=x, y=y)

        # Convert to PIL
        pil_point = vision_to_pil_coordinates(vision_point, height)

        # Convert back (inverse operation)
        back_to_vision = Point(x=pil_point.x, y=height - pil_point.y)

        # Should get back original point
        assert abs(back_to_vision.x - vision_point.x) < 0.0001
        assert abs(back_to_vision.y - vision_point.y) < 0.0001

    @given(
        x=st.floats(min_value=0, max_value=10000, allow_nan=False),
        image_height=st.floats(min_value=1, max_value=10000, allow_nan=False),
    )
    def test_vision_to_pil_x_unchanged(self, x, image_height):
        """Test that x coordinate is unchanged in vision to PIL conversion."""
        y = image_height / 2  # Arbitrary y
        vision_point = Point(x=x, y=y)

        pil_point = vision_to_pil_coordinates(vision_point, image_height)

        assert pil_point.x == vision_point.x

    @given(num_windows=st.integers(min_value=0, max_value=10), seed=st.integers())
    def test_parse_window_data_count(self, num_windows, seed):
        """Test that parse_window_data returns correct number of windows."""
        import random

        random.seed(seed)

        # Generate window data
        lines = []
        for i in range(num_windows):
            x = random.randint(0, 1000)
            y = random.randint(0, 1000)
            w = random.randint(100, 500)
            h = random.randint(100, 1000)
            lines.append(f"{i+1}, {x}, {y}, {w}, {h}, Test Window {i+1}")

        output = "\n".join(lines)
        windows = parse_window_data(output)

        assert len(windows) == num_windows

    @given(
        x1=st.floats(min_value=0, max_value=1000, allow_nan=False),
        y1=st.floats(min_value=0, max_value=1000, allow_nan=False),
        w1=st.floats(min_value=1, max_value=1000, allow_nan=False),
        h1=st.floats(min_value=1, max_value=1000, allow_nan=False),
        scale=st.floats(min_value=0.1, max_value=10, allow_nan=False),
    )
    def test_transform_scaling(self, x1, y1, w1, h1, scale):
        """Test that transformation scales correctly."""
        from_rect = Rectangle(x=0, y=0, width=w1, height=h1)
        to_rect = Rectangle(x=0, y=0, width=w1 * scale, height=h1 * scale)

        point = Point(x=x1, y=y1)
        assume(0 <= x1 <= w1)  # Point must be within rectangle
        assume(0 <= y1 <= h1)

        result = transform_coordinates(point, from_rect, to_rect)

        # Result should be scaled
        assert abs(result.x - x1 * scale) < 0.0001
        assert abs(result.y - y1 * scale) < 0.0001

    @given(
        points=st.lists(
            st.tuples(
                st.floats(min_value=0, max_value=1, allow_nan=False),
                st.floats(min_value=0, max_value=1, allow_nan=False),
            ),
            min_size=2,
            max_size=10,
        )
    )
    def test_transform_preserves_order(self, points):
        """Test that transformation preserves relative ordering of points."""
        from_rect = Rectangle(x=0, y=0, width=100, height=100)
        to_rect = Rectangle(x=0, y=0, width=200, height=200)

        # Convert normalized points to actual coordinates
        original_points = [Point(x=p[0] * 100, y=p[1] * 100) for p in points]

        # Transform all points
        transformed = [
            transform_coordinates(p, from_rect, to_rect) for p in original_points
        ]

        # Check that relative ordering is preserved
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                # If point i was left of point j, it should still be
                if original_points[i].x < original_points[j].x:
                    assert transformed[i].x <= transformed[j].x + 0.0001

                # If point i was above point j, it should still be
                if original_points[i].y < original_points[j].y:
                    assert transformed[i].y <= transformed[j].y + 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

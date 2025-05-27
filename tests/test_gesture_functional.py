"""Tests for the functional gesture controller using Quartz CoreGraphics."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.interact_types import (
    GesturePoint,
    SwipeGesture,
    MouseEvent,
    MouseEventSequence,
)

# Import Quartz constants for testing
try:
    from Quartz.CoreGraphics import (
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventLeftMouseDragged,
        kCGMouseButtonLeft,
    )
except ImportError:
    # Use same fallback values as in the controller
    kCGEventLeftMouseDown = 1
    kCGEventLeftMouseUp = 2
    kCGEventLeftMouseDragged = 6
    kCGMouseButtonLeft = 0

from ios_interact_mcp.gesture_controller import (
    create_swipe,
    create_tap,
    interpolate_points,
    generate_events,
    DIRECTION_UP,
    DIRECTION_DOWN,
    DIRECTION_LEFT,
    DIRECTION_RIGHT,
    SIMULATOR_MARGIN,
)


class TestPureGestureFunctions:
    """Test pure functions for gesture creation and manipulation."""

    def test_create_swipe_up(self):
        """Test creating swipe up gesture."""
        gesture = create_swipe(DIRECTION_UP, distance=200, center_x=100, center_y=400)

        assert gesture.start.x == 100
        assert gesture.start.y == 500  # center + distance/2
        assert gesture.end.x == 100
        assert gesture.end.y == 300  # start - distance

    def test_create_swipe_down(self):
        """Test creating swipe down gesture."""
        gesture = create_swipe(DIRECTION_DOWN, distance=150, center_x=100, center_y=275)

        assert gesture.start.x == 100
        assert gesture.start.y == 200  # center - distance/2
        assert gesture.end.x == 100
        assert gesture.end.y == 350  # start + distance

    def test_create_swipe_left(self):
        """Test creating swipe left gesture."""
        gesture = create_swipe(DIRECTION_LEFT, distance=100, center_x=250, center_y=400)

        assert gesture.start.x == 300  # center + distance/2
        assert gesture.start.y == 400
        assert gesture.end.x == 200  # start - distance
        assert gesture.end.y == 400

    def test_create_swipe_right(self):
        """Test creating swipe right gesture."""
        gesture = create_swipe(
            DIRECTION_RIGHT, distance=150, center_x=175, center_y=400
        )

        assert gesture.start.x == 100  # center - distance/2
        assert gesture.start.y == 400
        assert gesture.end.x == 250  # start + distance
        assert gesture.end.y == 400

    def test_interpolate_points(self):
        """Test point interpolation."""
        start = GesturePoint(x=0, y=0, pressure=0.5)
        end = GesturePoint(x=100, y=200, pressure=1.0)

        points = interpolate_points(start, end, steps=4)

        assert len(points) == 5  # steps + 1

        # Check interpolated values
        assert points[0].x == 0
        assert points[0].y == 0
        assert points[0].pressure == 0.5

        assert points[2].x == 50  # Midpoint
        assert points[2].y == 100
        assert points[2].pressure == 0.75

        assert points[4].x == 100
        assert points[4].y == 200
        assert points[4].pressure == 1.0

    def test_generate_tap_events_single(self):
        """Test generating events for single tap."""
        tap = create_tap(x=100, y=200)
        events = generate_events(tap)

        assert len(events.events) == 2  # Down and up

        # Check mouse down
        down = events.events[0]
        assert down.event_type == kCGEventLeftMouseDown
        assert down.x == 100
        assert down.y == 200
        assert down.button == kCGMouseButtonLeft
        assert down.timestamp_offset == 0.0

        # Check mouse up
        up = events.events[1]
        assert up.event_type == kCGEventLeftMouseUp
        assert up.x == 100
        assert up.y == 200
        assert up.timestamp_offset == tap.duration

    def test_generate_tap_events_double(self):
        """Test generating events for double tap."""
        tap = create_tap(x=150, y=250, tap_count=2)
        events = generate_events(tap)

        assert len(events.events) == 4  # 2 downs and 2 ups

        # First tap
        assert events.events[0].event_type == kCGEventLeftMouseDown
        assert events.events[0].timestamp_offset == 0.0
        assert events.events[1].event_type == kCGEventLeftMouseUp
        assert events.events[1].timestamp_offset == tap.duration

        # Second tap (with delay)
        assert events.events[2].event_type == kCGEventLeftMouseDown
        assert events.events[2].timestamp_offset > tap.duration  # Has delay
        assert events.events[3].event_type == kCGEventLeftMouseUp

    def test_generate_swipe_events(self):
        """Test generating events for swipe gesture."""
        swipe = SwipeGesture(
            start=GesturePoint(x=100, y=200),
            end=GesturePoint(x=300, y=400),
            duration=0.3,
            steps=3,
        )

        events = generate_events(swipe)

        # Should have: 1 down + 3 drags + 1 up = 5 events
        assert len(events.events) == 5

        # Check first event (mouse down)
        assert events.events[0].event_type == kCGEventLeftMouseDown
        assert events.events[0].x == 100
        assert events.events[0].y == 200
        assert events.events[0].timestamp_offset == 0.0

        # Check drag events
        for i in range(1, 4):
            assert events.events[i].event_type == kCGEventLeftMouseDragged

        # Check last event (mouse up)
        assert events.events[4].event_type == kCGEventLeftMouseUp
        assert events.events[4].x == 300
        assert events.events[4].y == 400
        assert events.events[4].timestamp_offset == swipe.duration

    def test_create_swipe_with_start_point(self):
        """Test creating swipe with explicit start point."""
        start = GesturePoint(x=100, y=200)
        gesture = create_swipe(DIRECTION_UP, distance=100, start=start)

        assert gesture.start.x == 100
        assert gesture.start.y == 200
        assert gesture.end.x == 100
        assert gesture.end.y == 100  # 200 - 100 (up direction)

    def test_scroll_gestures_as_swipes(self):
        """Test scroll gestures can be created as inverted swipes."""
        # Scroll up = swipe down
        scroll_up = create_swipe(
            DIRECTION_DOWN, distance=100, center_x=200, center_y=300
        )
        assert scroll_up.start.y < scroll_up.end.y  # Swipe down to scroll up

        # Scroll down = swipe up
        scroll_down = create_swipe(
            DIRECTION_UP, distance=100, center_x=200, center_y=300
        )
        assert scroll_down.start.y > scroll_down.end.y  # Swipe up to scroll down

    def test_page_navigation_swipes(self):
        """Test creating page navigation swipes manually."""
        from ios_interact_mcp.interact_types import SwipeGesture, GesturePoint

        screen_width = 390  # iPhone width
        screen_height = 844  # iPhone height
        margin = SIMULATOR_MARGIN

        # Navigate back (swipe right from left edge)
        back = SwipeGesture(
            start=GesturePoint(x=margin, y=screen_height / 2),
            end=GesturePoint(x=screen_width - margin, y=screen_height / 2),
            duration=0.4,
        )
        assert back.start.x < back.end.x
        assert back.start.x == 20  # margin

        # Navigate forward (swipe left from right edge)
        forward = SwipeGesture(
            start=GesturePoint(x=screen_width - margin, y=screen_height / 2),
            end=GesturePoint(x=margin, y=screen_height / 2),
            duration=0.4,
        )
        assert forward.start.x > forward.end.x
        assert forward.end.x == 20  # margin

    def test_mouse_event_at_time(self):
        """Test MouseEvent.at_time method."""
        event = MouseEvent(
            event_type=kCGEventLeftMouseDown,
            x=100,
            y=200,
            button=kCGMouseButtonLeft,
            timestamp_offset=0.5,
        )

        new_event = event.at_time(1.5)

        # Should keep all properties except timestamp
        assert new_event.event_type == event.event_type
        assert new_event.x == event.x
        assert new_event.y == event.y
        assert new_event.button == event.button
        assert new_event.timestamp_offset == 1.5

    def test_mouse_event_sequence_then(self):
        """Test MouseEventSequence.then method."""
        event1 = MouseEvent(
            event_type=kCGEventLeftMouseDown, x=100, y=200, button=kCGMouseButtonLeft
        )
        event2 = MouseEvent(
            event_type=kCGEventLeftMouseUp, x=100, y=200, button=kCGMouseButtonLeft
        )

        # Create sequence
        seq = MouseEventSequence(events=(event1,))

        # Add another event
        extended = seq.then(event2)

        # Original unchanged (immutable)
        assert len(seq.events) == 1

        # New sequence has both
        assert len(extended.events) == 2
        assert extended.events[0] == event1
        assert extended.events[1] == event2

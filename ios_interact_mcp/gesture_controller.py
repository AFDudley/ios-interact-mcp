"""
Functional Gesture Controller for iOS Simulator using Quartz CoreGraphics.

This module implements a functional programming approach to gesture control,
using macOS Quartz CoreGraphics for actual mouse event generation.
"""

import asyncio
from typing import List, Tuple, Optional, Union

from Quartz.CoreGraphics import (
    CGEventCreateMouseEvent,  # type: ignore[attr-defined]
    CGEventPost,  # type: ignore[attr-defined]
    kCGHIDEventTap,  # type: ignore[attr-defined]
    kCGEventLeftMouseDown,  # type: ignore[attr-defined]
    kCGEventLeftMouseUp,  # type: ignore[attr-defined]
    kCGEventLeftMouseDragged,  # type: ignore[attr-defined]
    kCGMouseButtonLeft,  # type: ignore[attr-defined]
)

from .interact_types import (
    GesturePoint,
    SwipeGesture,
    TapGesture,
    PinchGesture,
    GestureSequence,
    MouseEvent,
    MouseEventSequence,
    CommandResult,
    Window,
)
from .ocr_controller import observe_simulator
import subprocess


# ============================================================================
# Configuration
# ============================================================================


# Gesture configuration defaults
DEFAULT_SWIPE_DISTANCE = 200
DEFAULT_TAP_DURATION = 0.1
DEFAULT_SWIPE_DURATION = 0.3
DEFAULT_SWIPE_STEPS = 20
SIMULATOR_MARGIN = 20

# Direction vectors
DIRECTION_UP = (0, -1)
DIRECTION_DOWN = (0, 1)
DIRECTION_LEFT = (-1, 0)
DIRECTION_RIGHT = (1, 0)

# ============================================================================
# Focus Management
# ============================================================================


async def ensure_simulator_focused() -> None:
    """Ensure the iOS Simulator window is focused before performing gestures.

    Raises:
        RuntimeError: If simulator is not focused and cannot be focused
    """
    # Check if Simulator app is frontmost
    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get name of first application process whose frontmost is true',  # noqa: E501,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        frontmost_app = result.stdout.strip()

        # Check if simulator is already focused
        if "Simulator" in frontmost_app:
            return

        # Try to focus the simulator
        focus_result = subprocess.run(
            ["osascript", "-e", 'tell application "Simulator" to activate'],
            capture_output=True,
            text=True,
        )

        if focus_result.returncode != 0:
            raise RuntimeError("Failed to activate Simulator application")

        # Wait a moment for focus change to take effect
        await asyncio.sleep(0.5)

        # Verify simulator is now focused
        verify_result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get name of first application process whose frontmost is true',  # noqa: E501,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if "Simulator" not in verify_result.stdout:
            raise RuntimeError(
                "Simulator is not focused and could not be focused automatically"
            )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to check or set simulator focus: {e}")


# ============================================================================
# Pure Functions - No side effects, deterministic
# ============================================================================


def create_swipe(
    direction: Tuple[float, float],
    distance: Optional[float] = None,
    start: Optional[GesturePoint] = None,
    center_x: Optional[float] = None,
    center_y: Optional[float] = None,
    duration: Optional[float] = None,
    steps: Optional[int] = None,
) -> SwipeGesture:
    """Create a swipe gesture in any direction.

    Args:
        direction: Unit vector (dx, dy) indicating swipe direction
        distance: Distance to swipe in pixels
        start: Optional start point. If not provided, calculated from center
        center_x: X coordinate of swipe center (used if start not provided)
        center_y: Y coordinate of swipe center (used if start not provided)
        duration: Time duration for the swipe
        steps: Number of interpolation steps

    Returns:
        SwipeGesture ready to be performed
    """
    distance = distance or DEFAULT_SWIPE_DISTANCE
    duration = duration or DEFAULT_SWIPE_DURATION
    steps = steps or DEFAULT_SWIPE_STEPS

    # Calculate start point if not provided
    if start is None:
        # Note: center_x and center_y should be provided by caller
        # based on actual window dimensions
        if center_x is None or center_y is None:
            raise ValueError("Must provide either start point or center coordinates")

        # Start position is offset by half distance in opposite direction
        dx, dy = direction
        start = GesturePoint(
            x=center_x - (dx * distance / 2),
            y=center_y - (dy * distance / 2),
        )

    # Calculate end point
    dx, dy = direction
    end = GesturePoint(
        x=start.x + dx * distance,
        y=start.y + dy * distance,
        pressure=start.pressure,
    )

    return SwipeGesture(start=start, end=end, duration=duration, steps=steps)


def create_tap(x: float, y: float, tap_count: int = 1) -> TapGesture:
    """Create a tap gesture."""
    return TapGesture(point=GesturePoint(x=x, y=y), tap_count=tap_count)


def interpolate_points(
    start: GesturePoint, end: GesturePoint, steps: int
) -> List[GesturePoint]:
    """
    Interpolate points between start and end.

    Pure function that generates intermediate points for smooth gesture animation.
    """
    if steps <= 1:
        return [start, end]

    points = []
    for i in range(steps + 1):
        t = i / steps
        x = start.x + (end.x - start.x) * t
        y = start.y + (end.y - start.y) * t
        pressure = start.pressure + (end.pressure - start.pressure) * t
        points.append(GesturePoint(x=x, y=y, pressure=pressure))

    return points


def generate_events(gesture: Union[TapGesture, SwipeGesture]) -> MouseEventSequence:
    """Generate mouse events for any gesture type.

    Note: This returns low-level events. For actual gesture execution,
    use perform_gesture() which handles async I/O.

    Args:
        gesture: Either a TapGesture or SwipeGesture

    Returns:
        MouseEventSequence containing the events needed to perform the gesture
    """

    def _create_mouse_event(
        event_type: int,
        x: float,
        y: float,
        timestamp_offset: float = 0.0,
    ) -> MouseEvent:
        """Helper to create a mouse event with common parameters."""
        return MouseEvent(
            event_type=event_type,
            x=x,
            y=y,
            button=kCGMouseButtonLeft,
            timestamp_offset=timestamp_offset,
        )

    def mouse_down(x: float, y: float, timestamp_offset: float = 0.0) -> MouseEvent:
        """Create a mouse down event at the specified coordinates."""
        return _create_mouse_event(kCGEventLeftMouseDown, x, y, timestamp_offset)

    def mouse_up(x: float, y: float, timestamp_offset: float = 0.0) -> MouseEvent:
        """Create a mouse up event at the specified coordinates."""
        return _create_mouse_event(kCGEventLeftMouseUp, x, y, timestamp_offset)

    if isinstance(gesture, TapGesture):
        # Generate tap events: down/up pairs for each tap
        events = []
        for i in range(gesture.tap_count):
            tap_offset = i * (gesture.duration + 0.1)
            events.extend(
                [
                    mouse_down(gesture.point.x, gesture.point.y, tap_offset),
                    mouse_up(
                        gesture.point.x, gesture.point.y, tap_offset + gesture.duration
                    ),
                ]
            )
        return MouseEventSequence(events=tuple(events))

    elif isinstance(gesture, SwipeGesture):
        # Generate swipe events: down, drags, up
        points = interpolate_points(gesture.start, gesture.end, gesture.steps)
        time_per_step = gesture.duration / gesture.steps

        # Start with mouse down
        events = [mouse_down(gesture.start.x, gesture.start.y, 0.0)]

        # Add drags for intermediate points (skip first point)
        events.extend(
            [
                _create_mouse_event(
                    kCGEventLeftMouseDragged, point.x, point.y, i * time_per_step
                )
                for i, point in enumerate(points[1:], 1)
            ]
        )

        # End with mouse up
        events.append(mouse_up(gesture.end.x, gesture.end.y, gesture.duration))

        return MouseEventSequence(events=tuple(events))

    else:
        raise ValueError(f"Unknown gesture type: {type(gesture)}")


# ============================================================================
# Async I/O Functions - Side effects isolated here
# ============================================================================


async def post_mouse_event(event: MouseEvent) -> CommandResult:
    """
    Post a single mouse event using Quartz CoreGraphics.

    This is the ONLY function that performs I/O (posts events to the system).
    """
    try:
        # Create the mouse event
        cg_event = CGEventCreateMouseEvent(
            None, event.event_type, (event.x, event.y), event.button  # No event source
        )

        # Post the event
        CGEventPost(kCGHIDEventTap, cg_event)

        return CommandResult(
            success=True,
            output=f"Posted {event.event_type} at ({event.x}, {event.y})",
            error=None,
            exit_code=0,
        )

    except Exception as e:
        return CommandResult(success=False, output="", error=str(e), exit_code=-1)


# ============================================================================
# High-Level Functional API - Compose pure functions with I/O
# ============================================================================


async def perform_gesture(gesture: Union[TapGesture, SwipeGesture]) -> None:
    """Perform any supported gesture on the simulator."""
    events = generate_events(gesture)

    # Execute the event sequence with proper timing
    if not events.events:
        return

    last_timestamp = 0.0
    errors = []

    for event in events.events:
        # Wait for the right time
        if event.timestamp_offset > last_timestamp:
            wait_time = event.timestamp_offset - last_timestamp
            await asyncio.sleep(wait_time)
            last_timestamp = event.timestamp_offset

        # Post the event
        result = await post_mouse_event(event)
        if not result.success:
            errors.append(f"Event at {event.timestamp_offset}s: {result.error}")

    if errors:
        raise RuntimeError(
            f"Failed to perform {type(gesture).__name__}: {'; '.join(errors)}"
        )


async def perform_gesture_sequence(sequence: GestureSequence) -> None:
    """Perform a sequence of gestures."""
    # Ensure simulator is focused before performing gesture sequence
    await ensure_simulator_focused()

    for i, gesture in enumerate(sequence.gestures):
        if i > 0:
            await asyncio.sleep(sequence.delay_between)

        if isinstance(gesture, (SwipeGesture, TapGesture)):
            await perform_gesture(gesture)
        elif isinstance(gesture, PinchGesture):
            raise NotImplementedError("Pinch gestures not supported with mouse events")
        else:
            raise ValueError(f"Unknown gesture type: {type(gesture)}")


# ============================================================================
# Convenience Functions - High-level compositions
# ============================================================================


# Cache for simulator window information
# TODO: This cache is missing invalidation logic. Should be cleared when:
# - Simulator window is moved or resized
# - Different simulator is activated
# - Simulator is restarted
_cached_window: Optional[Window] = None


async def get_simulator_window() -> Optional[Window]:
    """Get cached simulator window information.

    Returns the first simulator window found, with position and dimensions.
    Results are cached to avoid repeated OCR calls.
    """
    global _cached_window
    if _cached_window is None:
        try:
            observation = await observe_simulator()
            if observation.windows:
                _cached_window = observation.windows[0]
        except Exception:
            pass
    return _cached_window


async def swipe_in_direction(
    direction: Tuple[float, float],
    distance: Optional[float] = None,
    center_x: Optional[float] = None,
    center_y: Optional[float] = None,
) -> None:
    """Perform a swipe in the specified direction within simulator window.

    Examples:
        # Swipe up
        await swipe_in_direction(DIRECTION_UP)

        # Swipe down with custom distance
        await swipe_in_direction(DIRECTION_DOWN, distance=300)

        # Swipe left from specific position
        await swipe_in_direction(DIRECTION_LEFT, center_x=200, center_y=400)

        # Scroll up (swipe down gesture)
        await swipe_in_direction(DIRECTION_DOWN)

        # Scroll down (swipe up gesture)
        await swipe_in_direction(DIRECTION_UP)
    """
    # Ensure simulator is focused before performing gesture
    await ensure_simulator_focused()

    window = await get_simulator_window()
    if not window:
        raise RuntimeError("No simulator window found")

    # Calculate absolute center coordinates if not specified
    if center_x is None:
        center_x = window.bounds.width / 2
    if center_y is None:
        center_y = window.bounds.height / 2

    # Calculate absolute start point
    dx, dy = direction
    absolute_start = GesturePoint(
        x=window.bounds.x + center_x - (dx * (distance or DEFAULT_SWIPE_DISTANCE) / 2),
        y=window.bounds.y + center_y - (dy * (distance or DEFAULT_SWIPE_DISTANCE) / 2),
    )

    # Create gesture with absolute coordinates
    gesture = create_swipe(direction, distance, start=absolute_start)
    await perform_gesture(gesture)


async def tap_at(x: float, y: float, tap_count: int = 1) -> None:
    """Tap at specific coordinates within simulator window.

    Args:
        x: X coordinate relative to simulator window
        y: Y coordinate relative to simulator window
        tap_count: Number of taps (1 for single tap, 2 for double tap, etc.)
    """
    # Ensure simulator is focused before performing gesture
    await ensure_simulator_focused()

    window = await get_simulator_window()
    if not window:
        raise RuntimeError("No simulator window found")

    gesture = create_tap(window.bounds.x + x, window.bounds.y + y, tap_count)
    await perform_gesture(gesture)

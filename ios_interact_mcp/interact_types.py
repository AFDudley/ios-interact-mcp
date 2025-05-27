"""
Type definitions for iOS simulator interaction.

This module contains immutable data structures used throughout the functional
OCR controller implementation.
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass(frozen=True)
class Point:
    """Immutable 2D point."""

    x: float
    y: float


@dataclass(frozen=True)
class Rectangle:
    """Immutable rectangle."""

    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> Point:
        """Calculate center point."""
        return Point(x=self.x + self.width / 2, y=self.y + self.height / 2)


@dataclass(frozen=True)
class Window:
    """Immutable window representation."""

    index: int
    bounds: Rectangle
    title: str


@dataclass(frozen=True)
class TextMatch:
    """Immutable text match result."""

    text: str
    confidence: float
    bounds: Rectangle


@dataclass(frozen=True)
class Screenshot:
    """Immutable screenshot data."""

    path: Path
    bounds: Rectangle
    timestamp: float


@dataclass(frozen=True)
class SimulatorObservation:
    """Complete observation of simulator state at a point in time."""

    windows: List[Window]
    is_fullscreen: bool
    active_window: Optional[Window]
    timestamp: float


@dataclass(frozen=True)
class ClickAction:
    """Description of a click action to perform."""

    screen_point: Point
    description: str


@dataclass(frozen=True)
class KeyboardAction:
    """Description of a keyboard action to perform."""

    key_combo: str
    description: str


@dataclass(frozen=True)
class ScreenshotAction:
    """Description of a screenshot action to perform."""

    window: Window
    output_path: Path


# XCRun Simulator Control Types


@dataclass(frozen=True)
class SimulatorCommand:
    """Immutable simulator command representation."""

    command: List[str]
    device: str = "booted"

    def to_args(self) -> List[str]:
        """Convert to xcrun simctl arguments."""
        # Handle device placement based on command
        if self.command and self.command[0] in [
            "launch",
            "terminate",
            "openurl",
            "get_app_container",
        ]:
            # These commands expect device after the command
            return self.command[:1] + [self.device] + self.command[1:]
        elif self.command and self.command[0] == "listapps":
            # listapps expects device after the command
            return ["listapps", self.device]
        else:
            # Default: command as-is (some commands don't need device)
            return self.command


@dataclass(frozen=True)
class CommandResult:
    """Immutable command execution result."""

    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0


@dataclass(frozen=True)
class App:
    """Immutable iOS app representation."""

    bundle_id: str
    display_name: str
    bundle_name: Optional[str] = None
    app_type: Optional[str] = None

    @property
    def name(self) -> str:
        """Get the best available name for the app."""
        return self.display_name or self.bundle_name or self.bundle_id


@dataclass(frozen=True)
class AppList:
    """Immutable collection of apps."""

    apps: tuple[App, ...]

    def find_by_bundle_id(self, bundle_id: str) -> Optional[App]:
        """Find app by bundle ID."""
        return next((app for app in self.apps if app.bundle_id == bundle_id), None)

    def find_by_name(self, name: str) -> Optional[App]:
        """Find app by display name (case-insensitive)."""
        name_lower = name.lower()
        return next((app for app in self.apps if app.name.lower() == name_lower), None)


@dataclass(frozen=True)
class DeviceInfo:
    """Immutable device information."""

    udid: str
    name: str
    state: str
    runtime: str
    device_type: str


# Gesture Control Types


@dataclass(frozen=True)
class GesturePoint:
    """Immutable point for gesture operations."""

    x: float
    y: float
    pressure: float = 1.0

    def offset(self, dx: float, dy: float) -> "GesturePoint":
        """Create a new point offset from this one."""
        return GesturePoint(x=self.x + dx, y=self.y + dy, pressure=self.pressure)


@dataclass(frozen=True)
class SwipeGesture:
    """Immutable swipe gesture description."""

    start: GesturePoint
    end: GesturePoint
    duration: float = 0.3  # seconds
    steps: int = 10  # number of interpolation steps

    def reverse(self) -> "SwipeGesture":
        """Create a reverse swipe."""
        return SwipeGesture(
            start=self.end, end=self.start, duration=self.duration, steps=self.steps
        )

    def with_duration(self, duration: float) -> "SwipeGesture":
        """Create a swipe with different duration."""
        return SwipeGesture(
            start=self.start, end=self.end, duration=duration, steps=self.steps
        )


@dataclass(frozen=True)
class TapGesture:
    """Immutable tap gesture description."""

    point: GesturePoint
    duration: float = 0.1  # seconds
    tap_count: int = 1


@dataclass(frozen=True)
class PinchGesture:
    """Immutable pinch gesture description."""

    center: GesturePoint
    start_distance: float
    end_distance: float
    duration: float = 0.3
    steps: int = 10

    @property
    def is_zoom_in(self) -> bool:
        """Check if this is a zoom in gesture."""
        return self.end_distance > self.start_distance


@dataclass(frozen=True)
class GestureSequence:
    """Immutable sequence of gestures."""

    gestures: tuple[SwipeGesture | TapGesture | PinchGesture, ...]
    delay_between: float = 0.1  # seconds

    def then(
        self, gesture: SwipeGesture | TapGesture | PinchGesture
    ) -> "GestureSequence":
        """Add another gesture to the sequence."""
        return GestureSequence(
            gestures=self.gestures + (gesture,), delay_between=self.delay_between
        )


@dataclass(frozen=True)
class MouseEvent:
    """Immutable mouse event description for Quartz CoreGraphics."""

    event_type: int  # kCGEventLeftMouseDown, kCGEventLeftMouseUp, etc.
    x: float
    y: float
    button: int  # kCGMouseButtonLeft, kCGMouseButtonRight, etc.
    timestamp_offset: float = 0.0  # Seconds from start of gesture

    def at_time(self, timestamp: float) -> "MouseEvent":
        """Create event with different timestamp."""
        return MouseEvent(
            event_type=self.event_type,
            x=self.x,
            y=self.y,
            button=self.button,
            timestamp_offset=timestamp,
        )


@dataclass(frozen=True)
class MouseEventSequence:
    """Immutable sequence of mouse events."""

    events: tuple[MouseEvent, ...]

    def then(self, event: MouseEvent) -> "MouseEventSequence":
        """Add another event to the sequence."""
        return MouseEventSequence(events=self.events + (event,))

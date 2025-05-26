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

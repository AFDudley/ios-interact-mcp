"""
Functional OCR Controller for iOS Simulator interaction.

This module implements a functional programming approach to simulator control,
emphasizing immutability, pure functions, and explicit side effects.
"""

import asyncio
import subprocess
from typing import List, Optional
from pathlib import Path
import tempfile
import os
from ocrmac import ocrmac
from PIL import Image

from .types import (
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


# ==========================
# Script Loading
# ==========================


def load_applescript(filename: str) -> str:
    """Load an AppleScript from the applescripts directory."""
    script_path = Path(__file__).parent / "applescripts" / filename
    if not script_path.exists():
        raise FileNotFoundError(f"AppleScript not found: {script_path}")
    return script_path.read_text()


# ==========================
# Pure Functions
# ==========================


def parse_window_data(output: str) -> List[Window]:
    """Parse AppleScript window output into Window objects."""
    windows = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split(", ")
        if len(parts) >= 5:
            try:
                window = Window(
                    index=int(parts[0]),
                    bounds=Rectangle(
                        x=float(parts[1]),
                        y=float(parts[2]),
                        width=float(parts[3]),
                        height=float(parts[4]),
                    ),
                    title=parts[5] if len(parts) > 5 else "",
                )
                windows.append(window)
            except (ValueError, IndexError):
                continue
    return windows


def transform_coordinates(
    point: Point, from_bounds: Rectangle, to_bounds: Rectangle
) -> Point:
    """Transform coordinates from one rectangle to another."""
    # Calculate relative position in source rectangle
    rel_x = (point.x - from_bounds.x) / from_bounds.width
    rel_y = (point.y - from_bounds.y) / from_bounds.height

    # Map to destination rectangle
    new_x = to_bounds.x + (rel_x * to_bounds.width)
    new_y = to_bounds.y + (rel_y * to_bounds.height)

    return Point(x=new_x, y=new_y)


def vision_to_pil_coordinates(vision_point: Point, image_height: float) -> Point:
    """Convert Vision framework coordinates to PIL coordinates."""
    # Vision uses bottom-left origin, PIL uses top-left
    return Point(x=vision_point.x, y=image_height - vision_point.y)


def parse_ocr_bounds(bounds_str: str) -> Rectangle:
    """Parse OCR bounds string into Rectangle."""
    # Format: "{{x, y}, {width, height}}"
    bounds_str = bounds_str.strip()
    if bounds_str.startswith("{{") and bounds_str.endswith("}}"):
        bounds_str = bounds_str[2:-2]
        parts = bounds_str.split("}, {")
        if len(parts) == 2:
            origin_parts = parts[0].split(", ")
            size_parts = parts[1].split(", ")
            if len(origin_parts) == 2 and len(size_parts) == 2:
                return Rectangle(
                    x=float(origin_parts[0]),
                    y=float(origin_parts[1]),
                    width=float(size_parts[0]),
                    height=float(size_parts[1]),
                )
    raise ValueError(f"Invalid bounds format: {bounds_str}")


def select_window(
    windows: List[Window], device_name: Optional[str] = None
) -> Optional[Window]:
    """Select a window based on device name or default to first."""
    if not windows:
        return None

    if device_name:
        for window in windows:
            if device_name.lower() in window.title.lower():
                return window

    return windows[0]


def calculate_click_point(
    text_match: TextMatch,
    screenshot_bounds: Rectangle,
    window_bounds: Rectangle,
    image_height: float,
) -> Point:
    """Calculate screen click point from text match."""
    # Get center of text in Vision coordinates
    vision_center = text_match.bounds.center

    # Convert to PIL coordinates
    pil_point = vision_to_pil_coordinates(vision_center, image_height)

    # Transform from screenshot space to screen space
    return transform_coordinates(pil_point, screenshot_bounds, window_bounds)


# ==========================
# Observation Functions (Side Effects)
# ==========================


async def observe_windows() -> List[Window]:
    """Observe current simulator windows."""
    result = await execute_osascript("enumerate_windows.applescript")
    return parse_window_data(result.stdout)


async def observe_simulator() -> SimulatorObservation:
    """Take a complete observation of simulator state."""
    import time

    windows = await observe_windows()

    return SimulatorObservation(
        windows=windows,
        is_fullscreen=False,  # Always False since we're not using fullscreen
        active_window=windows[0] if windows else None,
        timestamp=time.time(),
    )


# ==========================
# Effect Functions (Side Effects)
# ==========================


async def execute_osascript(script: str, *args: str) -> subprocess.CompletedProcess:
    """Execute an AppleScript and return the result.

    Args:
        script: The AppleScript to execute (can be inline or from file)
        *args: Optional arguments to pass to the script
    """
    # If script contains newlines, it's inline, otherwise it might be a filename
    if "\n" in script or not script.endswith(".applescript"):
        # Inline script
        cmd = ["osascript", "-e", script]
    else:
        # Script file
        script_path = Path(__file__).parent / "applescripts" / script
        if not script_path.exists():
            # Fallback to inline script
            cmd = ["osascript", "-e", script]
        else:
            cmd = ["osascript", str(script_path)]

    # Add arguments if provided
    cmd.extend(args)

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    result = subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode or 0,
        stdout=stdout.decode("utf-8"),
        stderr=stderr.decode("utf-8"),
    )

    if result.returncode != 0:
        raise RuntimeError(f"osascript failed: {result.stderr}")

    return result


async def execute_screenshot(action: ScreenshotAction) -> Screenshot:
    """Execute a screenshot action."""
    # Ensure output directory exists
    action.output_path.parent.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        "screencapture",
        "-R",
        f"{action.window.bounds.x},{action.window.bounds.y},"
        f"{action.window.bounds.width},{action.window.bounds.height}",
        str(action.output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Screenshot failed: {stderr.decode('utf-8')}")

    if not action.output_path.exists():
        raise RuntimeError(f"Screenshot file not created at {action.output_path}")

    import time

    return Screenshot(
        path=action.output_path, bounds=action.window.bounds, timestamp=time.time()
    )


async def execute_click(action: ClickAction) -> None:
    """Execute a click action."""
    await execute_osascript(
        "click_at_coordinates.applescript",
        str(int(action.screen_point.x)),
        str(int(action.screen_point.y)),
    )


async def execute_keyboard(action: KeyboardAction) -> None:
    """Execute a keyboard action."""
    await execute_osascript("send_keystroke.applescript", action.key_combo)


# ==========================
# OCR Functions
# ==========================


def perform_ocr(image_path: Path, search_text: Optional[str] = None) -> List[TextMatch]:
    """Perform OCR on an image and return text matches."""
    annotations = ocrmac.OCR(str(image_path)).recognize()

    # Get image dimensions for coordinate conversion
    with Image.open(image_path) as img:
        image_width = img.width
        image_height = img.height

    matches = []
    for annotation in annotations:
        if len(annotation) >= 3:
            text = annotation[0]
            confidence = annotation[1]
            # Bounds are in format: [x, y, width, height] as normalized coordinates
            norm_bounds = annotation[2]

            if search_text is None or search_text.lower() in text.lower():
                # Convert normalized coordinates to pixel coordinates
                bounds = Rectangle(
                    x=norm_bounds[0] * image_width,
                    y=norm_bounds[1] * image_height,
                    width=norm_bounds[2] * image_width,
                    height=norm_bounds[3] * image_height,
                )
                matches.append(
                    TextMatch(text=text, confidence=confidence, bounds=bounds)
                )

    return matches


# ==========================
# High-Level Functions
# ==========================


async def find_text_in_simulator(
    search_text: Optional[str] = None, device_name: Optional[str] = None
) -> str:
    """Find text in simulator using functional approach."""
    # Observe current state
    observation = await observe_simulator()

    # Select target window
    window = select_window(observation.windows, device_name)
    if not window:
        raise RuntimeError("No simulator windows found")

    # Create screenshot action
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        screenshot_action = ScreenshotAction(window=window, output_path=Path(tmp.name))

    try:
        # Execute screenshot
        screenshot = await execute_screenshot(screenshot_action)

        # Perform OCR
        matches = perform_ocr(screenshot.path, search_text)

        # Format results
        results = [
            f"{'Found ' if search_text else ''}'{match.text}' at {match.bounds}"
            for match in matches
        ]
        if not results:
            return f"Text '{search_text}' not found" if search_text else "No text found"
        return "\n".join(results)

    finally:
        # Cleanup screenshot
        if screenshot_action.output_path.exists():
            os.unlink(screenshot_action.output_path)


async def click_text_in_simulator(
    text: str, occurrence: int = 1, device_name: Optional[str] = None
) -> None:
    """Click on text in simulator using functional approach."""
    # Observe current state
    observation = await observe_simulator()

    # Select target window
    window = select_window(observation.windows, device_name)
    if not window:
        raise RuntimeError("No simulator windows found")

    # Create screenshot action
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        screenshot_action = ScreenshotAction(window=window, output_path=Path(tmp.name))

    try:
        # Execute screenshot
        screenshot = await execute_screenshot(screenshot_action)

        # Perform OCR
        matches = perform_ocr(screenshot.path, text)

        if not matches:
            raise ValueError(f"Text '{text}' not found in simulator")

        if occurrence > len(matches):
            raise ValueError(
                f"Only {len(matches)} occurrences of '{text}' found, "
                f"requested occurrence {occurrence}"
            )

        # Get target match
        target_match = matches[occurrence - 1]

        # Get image dimensions for coordinate conversion
        with Image.open(screenshot.path) as img:
            image_width = img.width
            image_height = img.height

        # Calculate click point
        # OCR coordinates are in screenshot pixel space (0,0 to width,height)
        # We need to transform them to screen coordinates
        screenshot_pixel_bounds = Rectangle(
            x=0, y=0, width=image_width, height=image_height
        )
        click_point = calculate_click_point(
            target_match, screenshot_pixel_bounds, window.bounds, image_height
        )

        # Create and execute click action
        click_action = ClickAction(
            screen_point=click_point,
            description=f"Click on '{text}' (occurrence {occurrence})",
        )

        await execute_click(click_action)

    finally:
        # Cleanup screenshot
        if screenshot_action.output_path.exists():
            os.unlink(screenshot_action.output_path)


async def click_at_coordinates(
    x: int, y: int, coordinate_space: str = "screen"
) -> None:
    """Click at specific coordinates using functional approach."""
    if coordinate_space == "screen":
        # Direct screen coordinates
        click_action = ClickAction(
            screen_point=Point(x=x, y=y),
            description=f"Click at screen coordinates ({x}, {y})",
        )
        await execute_click(click_action)

    elif coordinate_space == "device":
        # Device coordinates - need to transform
        observation = await observe_simulator()

        if not observation.active_window:
            raise RuntimeError("No simulator windows found")

        # Transform from device space to screen space
        device_bounds = Rectangle(x=0, y=0, width=390, height=844)  # iPhone 14 default
        screen_point = transform_coordinates(
            Point(x=x, y=y), device_bounds, observation.active_window.bounds
        )

        click_action = ClickAction(
            screen_point=screen_point,
            description=f"Click at device coordinates ({x}, {y})",
        )
        await execute_click(click_action)

    else:
        raise ValueError(f"Invalid coordinate_space: {coordinate_space}")


async def ensure_fullscreen() -> bool:
    """Ensure simulator is in fullscreen mode. Returns True if state was changed."""
    # Check current state by reading menu
    try:
        result = await execute_osascript("check_fullscreen_menu.applescript")
        # If "Exit Full Screen" is in menu, we ARE in fullscreen
        # If "Enter Full Screen" is in menu, we're NOT in fullscreen
        is_fullscreen = "Exit Full Screen" in result.stdout
    except Exception as e:
        # If we can't read the menu, fail fast
        raise RuntimeError(f"Failed to read fullscreen menu state: {e}")

    if is_fullscreen:
        # Already in fullscreen
        return False

    # Enter fullscreen with toggle script
    await execute_osascript("toggle_fullscreen.applescript")

    # Wait for state change (longer delay for fullscreen transition)
    await asyncio.sleep(2.0)

    # Verify state change by checking menu again
    try:
        result = await execute_osascript("check_fullscreen_menu.applescript")
        new_is_fullscreen = "Exit Full Screen" in result.stdout
    except Exception as e:
        # If we can't verify, fail with details
        raise RuntimeError(f"Failed to verify fullscreen state: {e}")

    if not new_is_fullscreen:
        raise RuntimeError("Failed to enter fullscreen")

    return True


async def exit_fullscreen() -> None:
    """Exit fullscreen mode to return to windowed mode."""
    # Observe current state
    observation = await observe_simulator()

    if not observation.is_fullscreen:
        # Already in windowed mode
        return

    # Exit fullscreen with toggle script
    await execute_osascript("toggle_fullscreen.applescript")

    # Wait for state change
    await asyncio.sleep(2.0)

    # Verify state change
    new_observation = await observe_simulator()
    if new_observation.is_fullscreen:
        raise RuntimeError("Failed to exit fullscreen")


async def setup_clean_simulator_state() -> None:
    """Set up clean simulator state: windowed mode, home screen, Settings app closed."""
    await execute_osascript("setup_clean_state.applescript")


async def open_settings_app() -> None:
    """Open the iOS Settings app using xcrun simctl."""
    await execute_osascript("open_settings_app.applescript")


async def save_screenshot(output_path: str, device_name: Optional[str] = None) -> str:
    """Save a screenshot of the simulator."""
    # Observe current state
    observation = await observe_simulator()

    # Select target window
    window = select_window(observation.windows, device_name)
    if not window:
        raise RuntimeError("No simulator windows found")

    # Create screenshot action
    screenshot_action = ScreenshotAction(window=window, output_path=Path(output_path))

    # Execute screenshot
    screenshot = await execute_screenshot(screenshot_action)

    return str(screenshot.path)

#!/usr/bin/env python3
"""
iOS Interact MCP Server
Provides tools for controlling both iOS Simulator and real iOS devices
via xcrun simctl and xcrun devicectl commands.

This server enables Claude Code to interact with iOS apps on simulators
and physical devices on macOS using only stock tools.
"""

import argparse
from typing import Optional

from mcp.server.fastmcp import FastMCP

from . import ocr_controller as ocr
from . import xcrun_controller as xcrun
from . import gesture_controller as gesture

# Create FastMCP server instance
mcp = FastMCP("ios-interact-server")


@mcp.tool()
async def click_at_coordinates(x: int, y: int, coordinate_space: str = "screen") -> str:
    """Click at specific coordinates

    Args:
        x: X coordinate
        y: Y coordinate
        coordinate_space: Either "screen" for absolute screen coordinates or
                          "device" for device coordinates
    """
    await ocr.click_at_coordinates(x, y, coordinate_space)
    return f"Clicked at coordinates ({x}, {y})"


@mcp.tool()
async def click_text(
    text: str, occurrence: int = 1, device_name: Optional[str] = None
) -> str:
    """Click on text found in the simulator using OCR

    Args:
        text: Text to search for and click on
        occurrence: Which occurrence to click (1-based index)
        device_name: Optional device name to target
    """
    await ocr.click_text_in_simulator(text, occurrence, device_name)
    return f"Clicked on '{text}'"


@mcp.tool()
async def launch_app(bundle_id: str) -> str:
    """Launch an iOS app in the simulator"""
    pid = await xcrun.launch_app(bundle_id)
    if pid:
        return f"Successfully launched {bundle_id} (PID: {pid})"
    else:
        return f"Successfully launched {bundle_id}"


@mcp.tool()
async def terminate_app(bundle_id: str) -> str:
    """Terminate a running iOS app"""
    await xcrun.terminate_app(bundle_id)
    return f"Successfully terminated {bundle_id}"


@mcp.tool()
async def screenshot(filename: Optional[str] = None, return_path: bool = True) -> str:
    """Take a screenshot of the iOS simulator using OCR capture

    Args:
        filename: Optional filename. If not provided, generates timestamp-based name.
                 If relative path, saves to Desktop. If absolute path, uses as-is.
        return_path: Whether to return the file path in the response
    """
    import os
    import time

    # Generate filename with timestamp if not provided
    if filename is None:
        timestamp = int(time.time() * 1000)
        filename = f"ios_screenshot_{timestamp}.png"

    # Ensure the file goes to an accessible location
    if not os.path.isabs(filename):
        # Default to Desktop for easy user access
        desktop_path = os.path.expanduser("~/Desktop")
        filename = os.path.join(desktop_path, filename)

    path = await ocr.save_screenshot(filename)
    if return_path:
        return f"Screenshot saved to: {path}"
    else:
        return "Screenshot captured successfully"


@mcp.tool()
async def list_apps() -> str:
    """List all installed apps on the simulator"""
    return await xcrun.list_apps()


@mcp.tool()
async def open_url(url: str) -> str:
    """Open a URL in the simulator (useful for deep linking)"""
    await xcrun.open_url(url)
    return f"Successfully opened URL: {url}"


@mcp.tool()
async def get_app_container(bundle_id: str, container_type: str = "data") -> str:
    """Get the app container path for file access"""
    path = await xcrun.get_app_container(bundle_id, container_type)
    return str(path)


@mcp.tool()
async def list_simulator_windows() -> str:
    """List all simulator windows with their positions and sizes"""
    windows = await ocr.observe_windows()
    if not windows:
        return "No simulator windows found. Make sure iOS Simulator is running."

    results = [f"Found {len(windows)} simulator window(s):"]
    for window in windows:
        results.append(
            f"{window.index}. {window.title}\n"
            f"   Position: ({window.bounds.x}, {window.bounds.y})\n"
            f"   Size: {window.bounds.width}x{window.bounds.height}"
        )
    return "\n".join(results)


@mcp.tool()
async def find_text_in_simulator(
    search_text: Optional[str] = None, device_name: Optional[str] = None
) -> str:
    """Find text in the simulator screen using OCR

    Args:
        search_text: Optional text to search for. If None, returns all visible text.
        device_name: Optional device name to target. If None, uses first simulator.
    """
    import tempfile
    from pathlib import Path

    # Observe current state
    observation = await ocr.observe_simulator()

    # Select target window
    window = ocr.select_window(observation.windows, device_name)
    if not window:
        return "No simulator windows found. Make sure iOS Simulator is running."

    # Create screenshot action
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        screenshot_action = ocr.ScreenshotAction(
            window=window, output_path=Path(tmp.name)
        )

    try:
        # Execute screenshot
        screenshot = await ocr.execute_screenshot(screenshot_action)

        # Perform OCR
        matches = ocr.perform_ocr(screenshot.path, search_text)

        if not matches:
            return f"Text '{search_text}' not found" if search_text else "No text found"

        # Format results with center coordinates
        results = []
        for i, match in enumerate(matches, 1):
            center = match.bounds.center
            results.append(f"{i}. '{match.text}' at ({int(center.x)}, {int(center.y)})")

        return f"Found {len(matches)} occurrence(s) of '{search_text}':\n" + "\n".join(
            results
        )

    finally:
        # Cleanup screenshot
        import os

        if screenshot_action.output_path.exists():
            os.unlink(screenshot_action.output_path)


@mcp.tool()
async def press_button(button_name: str) -> str:
    """Press a hardware button on the simulator

    Args:
        button_name: Name of the button
                     (e.g., 'home', 'lock', 'volume_up', 'volume_down')
    """
    await xcrun.press_button(button_name)
    return f"Pressed {button_name} button"


@mcp.tool()
async def swipe(direction: str, distance: float = 200) -> str:
    """Perform a swipe gesture in the specified direction

    Args:
        direction: Direction to swipe ('up', 'down', 'left', 'right')
        distance: Distance to swipe in pixels (default: 200)
    """
    direction_map = {
        "up": gesture.DIRECTION_UP,
        "down": gesture.DIRECTION_DOWN,
        "left": gesture.DIRECTION_LEFT,
        "right": gesture.DIRECTION_RIGHT,
    }

    if direction not in direction_map:
        return f"Invalid direction: {direction}. Use 'up', 'down', 'left', or 'right'"

    await gesture.swipe_in_direction(direction_map[direction], distance)
    return f"Swiped {direction} {distance} pixels"


@mcp.tool()
async def scroll(direction: str, distance: float = 200) -> str:
    """Scroll in the specified direction

    Args:
        direction: Direction to scroll ('up', 'down')
        distance: Distance to scroll in pixels (default: 200)
    """
    # Scroll is inverted - scroll up means swipe down
    scroll_map = {
        "up": gesture.DIRECTION_DOWN,
        "down": gesture.DIRECTION_UP,
    }

    if direction not in scroll_map:
        return f"Invalid direction: {direction}. Use 'up' or 'down'"

    await gesture.swipe_in_direction(scroll_map[direction], distance)
    return f"Scrolled {direction} {distance} pixels"


@mcp.tool()
async def tap_coordinates(x: float, y: float, tap_count: int = 1) -> str:
    """Tap at specific coordinates

    Args:
        x: X coordinate
        y: Y coordinate
        tap_count: Number of taps (1 for single tap, 2 for double tap)
    """
    await gesture.tap_at(x, y, tap_count)

    if tap_count == 1:
        return f"Tapped at ({x}, {y})"
    elif tap_count == 2:
        return f"Double tapped at ({x}, {y})"
    else:
        return f"Tapped {tap_count} times at ({x}, {y})"


def main():
    """Entry point for the MCP server"""
    parser = argparse.ArgumentParser(description="iOS Interact MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport type: stdio for Claude Desktop, sse for Claude Code "
        "(default: stdio)",
    )

    args = parser.parse_args()

    # Run with specified transport
    if args.transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()

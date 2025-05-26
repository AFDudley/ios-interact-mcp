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

from . import ocr_controller_functional as ocr
from .xcrun_controller import SimulatorController

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
    _, message = await SimulatorController.launch_app(bundle_id)
    return message


@mcp.tool()
async def terminate_app(bundle_id: str) -> str:
    """Terminate a running iOS app"""
    _, message = await SimulatorController.terminate_app(bundle_id)
    return message


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
    _, message = await SimulatorController.list_apps()
    return message


@mcp.tool()
async def open_url(url: str) -> str:
    """Open a URL in the simulator (useful for deep linking)"""
    _, message = await SimulatorController.open_url(url)
    return message


@mcp.tool()
async def get_app_container(bundle_id: str, container_type: str = "data") -> str:
    """Get the app container path for file access"""
    _, message = await SimulatorController.get_app_container(bundle_id, container_type)
    return message


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
    return await ocr.find_text_in_simulator(search_text, device_name)


@mcp.tool()
async def press_button(button_name: str) -> str:
    """Press a hardware button on the simulator

    Args:
        button_name: Name of the button
                     (e.g., 'home', 'lock', 'volume_up', 'volume_down')
    """
    _, message = await SimulatorController.press_button(button_name)
    return message


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

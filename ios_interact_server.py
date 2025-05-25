#!/usr/bin/env python3
"""
iOS Interact MCP Server
Provides tools for controlling both iOS Simulator and real iOS devices
via xcrun simctl and xcrun devicectl commands.

This server enables Claude Code to interact with iOS apps on simulators
and physical devices on macOS using only stock tools.
"""

import asyncio
import subprocess
import json
import os
import sys
import argparse
from typing import Any, Optional
from pathlib import Path
import time

from mcp.server.fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("ios-interact-server")

class SimulatorController:
    """Wrapper for xcrun simctl commands"""
    
    @staticmethod
    def run_command(args: list[str]) -> tuple[bool, str]:
        """Run a simctl command and return success status and output"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl"] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr or e.stdout or str(e)
    
    @staticmethod
    async def run_command_async(args: list[str]) -> tuple[bool, str]:
        """Async version of run_command"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return True, stdout.decode().strip()
            else:
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                return False, error_msg
        except Exception as e:
            return False, str(e)

@mcp.tool()
async def launch_app(bundle_id: str) -> str:
    """Launch an iOS app in the simulator"""
    controller = SimulatorController()
    success, output = await controller.run_command_async(["launch", "booted", bundle_id])
    
    if success:
        return f"Successfully launched {bundle_id}"
    else:
        return f"Failed to launch {bundle_id}: {output}"

@mcp.tool()
async def terminate_app(bundle_id: str) -> str:
    """Terminate a running iOS app"""
    controller = SimulatorController()
    success, output = await controller.run_command_async(["terminate", "booted", bundle_id])
    
    if success:
        return f"Successfully terminated {bundle_id}"
    else:
        return f"Failed to terminate {bundle_id}: {output}"

@mcp.tool()
async def screenshot(filename: Optional[str] = None, return_path: bool = True) -> str:
    """Take a screenshot of the iOS simulator
    
    Args:
        filename: Optional filename. If not provided, generates timestamp-based name.
                 If relative path, saves to Desktop. If absolute path, uses as-is.
        return_path: Whether to return the file path in the response
    """
    controller = SimulatorController()
    
    # Generate filename with timestamp if not provided
    timestamp = int(time.time() * 1000)
    if filename is None:
        filename = f"ios_screenshot_{timestamp}.png"
    
    # Ensure the file goes to an accessible location
    if not os.path.isabs(filename):
        # Default to Desktop for easy user access
        desktop_path = os.path.expanduser("~/Desktop")
        filename = os.path.join(desktop_path, filename)
    
    # Ensure the directory exists
    directory = os.path.dirname(filename)
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        return f"Failed to create directory {directory}: {e}"
    
    # Verify we can write to the location
    if not os.access(directory, os.W_OK):
        return f"Cannot write to directory: {directory}"
    
    success, output = await controller.run_command_async(["io", "booted", "screenshot", filename])
    
    if success:
        # Verify the file was actually created
        if os.path.exists(filename):
            if return_path:
                return f"Screenshot saved to: {filename}"
            else:
                return "Screenshot captured successfully"
        else:
            return f"Screenshot command succeeded but file not found at: {filename}"
    else:
        return f"Failed to capture screenshot: {output}"

@mcp.tool()
async def list_apps() -> str:
    """List all installed apps on the simulator"""
    controller = SimulatorController()
    success, output = await controller.run_command_async(["listapps", "booted"])
    
    if success:
        try:
            # Parse the JSON output
            apps_data = json.loads(output)
            apps_list = []
            
            for bundle_id, app_info in apps_data.items():
                app_name = app_info.get("CFBundleDisplayName", app_info.get("CFBundleName", "Unknown"))
                apps_list.append(f"• {app_name} ({bundle_id})")
            
            if apps_list:
                return f"Installed apps ({len(apps_list)}):\n" + "\n".join(sorted(apps_list))
            else:
                return "No apps found on the simulator"
                
        except json.JSONDecodeError:
            # Fallback for non-JSON output
            return f"Apps list (raw output):\n{output}"
    else:
        return f"Failed to list apps: {output}"

@mcp.tool()
async def open_url(url: str) -> str:
    """Open a URL in the simulator (useful for deep linking)"""
    controller = SimulatorController()
    success, output = await controller.run_command_async(["openurl", "booted", url])
    
    if success:
        return f"Successfully opened URL: {url}"
    else:
        return f"Failed to open URL: {output}"

@mcp.tool()
async def get_app_container(bundle_id: str, container_type: str = "data") -> str:
    """Get the app container path for file access"""
    controller = SimulatorController()
    
    success, output = await controller.run_command_async([
        "get_app_container", "booted", bundle_id, container_type
    ])
    
    if success:
        container_path = output.strip()
        return f"App container path ({container_type}):\n{container_path}"
    else:
        return f"Failed to get app container: {output}"

def main():
    """Entry point for the MCP server"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='iOS Interact MCP Server')
    parser.add_argument('--transport', 
                       choices=['stdio', 'sse'], 
                       default='stdio',
                       help='Transport type: stdio for Claude Desktop, sse for Claude Code (default: stdio)')
    
    args = parser.parse_args()
    
    # Run with specified transport
    if args.transport == 'sse':
        # SSE transport for Claude Code
        mcp.run(transport="sse")
    else:
        # stdio transport for Claude Desktop (default)
        mcp.run()

if __name__ == "__main__":
    main()


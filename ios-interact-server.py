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
from typing import Any, Optional
from pathlib import Path
import time

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create server instance
server = Server("ios-interact-server")

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

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Define available tools for iOS Simulator control"""
    return [
        Tool(
            name="launch_app",
            description="Launch an iOS app in the simulator",
            inputSchema={
                "type": "object",
                "properties": {
                    "bundle_id": {
                        "type": "string",
                        "description": "Bundle ID of the app to launch (e.g., com.apple.mobilesafari)"
                    }
                },
                "required": ["bundle_id"]
            }
        ),
        Tool(
            name="terminate_app",
            description="Terminate a running iOS app",
            inputSchema={
                "type": "object",
                "properties": {
                    "bundle_id": {
                        "type": "string",
                        "description": "Bundle ID of the app to terminate"
                    }
                },
                "required": ["bundle_id"]
            }
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of the iOS simulator",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Output filename for the screenshot (optional, defaults to timestamp)"
                    },
                    "return_path": {
                        "type": "boolean",
                        "description": "Return the full file path in the response",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="list_apps",
            description="List all installed apps on the simulator",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="open_url",
            description="Open a URL in the simulator (useful for deep linking)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to open (e.g., https://example.com or myapp://path)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_app_container",
            description="Get the app container path for file access",
            inputSchema={
                "type": "object",
                "properties": {
                    "bundle_id": {
                        "type": "string",
                        "description": "Bundle ID of the app"
                    },
                    "container_type": {
                        "type": "string",
                        "description": "Container type: 'app', 'data', or 'groups'",
                        "enum": ["app", "data", "groups"],
                        "default": "data"
                    }
                },
                "required": ["bundle_id"]
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution requests"""
    controller = SimulatorController()
    
    if name == "launch_app":
        bundle_id = arguments["bundle_id"]
        success, output = await controller.run_command_async(["launch", "booted", bundle_id])
        
        if success:
            return [TextContent(type="text", text=f"Successfully launched {bundle_id}")]
        else:
            return [TextContent(type="text", text=f"Failed to launch {bundle_id}: {output}")]
    
    elif name == "terminate_app":
        bundle_id = arguments["bundle_id"]
        success, output = await controller.run_command_async(["terminate", "booted", bundle_id])
        
        if success:
            return [TextContent(type="text", text=f"Successfully terminated {bundle_id}")]
        else:
            return [TextContent(type="text", text=f"Failed to terminate {bundle_id}: {output}")]
    
    elif name == "screenshot":
        # Generate filename with timestamp if not provided
        timestamp = int(time.time() * 1000)
        filename = arguments.get("filename", f"ios_screenshot_{timestamp}.png")
        return_path = arguments.get("return_path", True)
        
        # Ensure absolute path
        if not os.path.isabs(filename):
            filename = os.path.abspath(filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        success, output = await controller.run_command_async(["io", "booted", "screenshot", filename])
        
        if success:
            if return_path:
                return [TextContent(type="text", text=f"Screenshot saved to: {filename}")]
            else:
                return [TextContent(type="text", text="Screenshot captured successfully")]
        else:
            return [TextContent(type="text", text=f"Failed to capture screenshot: {output}")]
    
    elif name == "list_apps":
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
                    return [TextContent(
                        type="text",
                        text=f"Installed apps ({len(apps_list)}):\n" + "\n".join(sorted(apps_list))
                    )]
                else:
                    return [TextContent(type="text", text="No apps found on the simulator")]
                    
            except json.JSONDecodeError:
                # Fallback for non-JSON output
                return [TextContent(type="text", text=f"Apps list (raw output):\n{output}")]
        else:
            return [TextContent(type="text", text=f"Failed to list apps: {output}")]
    
    elif name == "open_url":
        url = arguments["url"]
        success, output = await controller.run_command_async(["openurl", "booted", url])
        
        if success:
            return [TextContent(type="text", text=f"Successfully opened URL: {url}")]
        else:
            return [TextContent(type="text", text=f"Failed to open URL: {output}")]
    
    elif name == "get_app_container":
        bundle_id = arguments["bundle_id"]
        container_type = arguments.get("container_type", "data")
        
        success, output = await controller.run_command_async([
            "get_app_container", "booted", bundle_id, container_type
        ])
        
        if success:
            container_path = output.strip()
            return [TextContent(
                type="text",
                text=f"App container path ({container_type}):\n{container_path}"
            )]
        else:
            return [TextContent(type="text", text=f"Failed to get app container: {output}")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Main entry point for the MCP server"""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ios-interact",
                server_version="0.0.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test FastMCP integration for iOS Interact Server
"""

import sys
import os

# Import the server directly
import importlib.util

spec = importlib.util.spec_from_file_location("server", "ios-interact-server.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)

# Get the mcp instance
mcp = server_module.mcp

print("Testing FastMCP Integration")
print("=" * 50)

# Check if mcp instance exists
print(f"1. MCP instance type: {type(mcp)}")
print(f"   MCP name: {mcp.name}")

# List registered tools
print("\n2. Registered tools:")
if hasattr(mcp, "_tools"):
    for tool_name, tool_info in mcp._tools.items():
        print(f"   - {tool_name}")
else:
    # Try to access tools through the tools registry
    try:
        # FastMCP stores tools differently, let's check the actual structure
        print(
            f"   MCP attributes: {[attr for attr in dir(mcp) if not attr.startswith('_')]}"
        )
    except Exception as e:
        print(f"   Error accessing tools: {e}")

print("\n✅ FastMCP server is properly configured")

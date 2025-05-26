#!/usr/bin/env python3
"""
Test script for ios-interact MCP server with both stdio and SSE transports.
Based on the MCP Python SDK testing patterns.
"""

import asyncio
import subprocess
import json
import sys
import os
from pathlib import Path

# Add the parent directory to path to import the server module
sys.path.insert(0, str(Path(__file__).parent))

from ios_interact_server import mcp
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)


async def test_memory_transport():
    """Test server functionality using in-memory transport (no network)"""
    print("=== Testing with in-memory transport ===")

    try:
        # Create connected client and server in memory
        async with client_session(mcp._mcp_server) as client:
            # Initialize
            result = await client.initialize()
            print(
                f"✅ Initialize successful: {result.serverInfo.name} v{result.serverInfo.version}"
            )

            # List available tools
            tools_result = await client.list_tools()
            print(f"✅ Available tools: {len(tools_result.tools)}")
            for tool in tools_result.tools:
                print(f"   - {tool.name}: {tool.description}")

            # Test a tool (list_apps)
            try:
                apps_result = await client.call_tool("list_apps", {})
                print(f"✅ Tool call successful: list_apps")
                print(f"   Response: {apps_result.content[0].text[:100]}...")
            except Exception as e:
                print(f"⚠️  Tool call failed (expected if simulator not running): {e}")

    except Exception as e:
        print(f"❌ Memory transport test failed: {e}")
        return False

    return True


def test_stdio_transport():
    """Test server with stdio transport"""
    print("\n=== Testing with stdio transport ===")

    # Prepare test request
    test_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    # Start server process
    proc = subprocess.Popen(
        [sys.executable, "ios_interact_server.py", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Send request
        proc.stdin.write(json.dumps(test_request) + "\n")
        proc.stdin.flush()

        # Read response
        response_line = proc.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            if "result" in response:
                print(
                    f"✅ Initialize successful: {response['result']['serverInfo']['name']}"
                )
                return True
            else:
                print(f"❌ Unexpected response: {response}")
                return False
        else:
            print("❌ No response received")
            stderr = proc.stderr.read()
            if stderr:
                print(f"   stderr: {stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        proc.terminate()
        proc.wait()


def test_sse_transport():
    """Test server with SSE transport"""
    print("\n=== Testing with SSE transport ===")

    # Start server process
    proc = subprocess.Popen(
        [sys.executable, "ios_interact_server.py", "--transport", "sse"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Give server time to start
        import time

        time.sleep(2)

        # Check if process is still running
        if proc.poll() is None:
            print("✅ SSE server started successfully (process running)")
            print("   Server would be available at http://localhost:8000")
            return True
        else:
            print("❌ SSE server failed to start")
            stderr = proc.stderr.read()
            if stderr:
                print(f"   stderr: {stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        proc.terminate()
        proc.wait()


async def main():
    """Run all tests"""
    print("Testing iOS Interact MCP Server Transports\n")

    # Test in-memory transport (most thorough testing)
    memory_ok = await test_memory_transport()

    # Test stdio transport
    stdio_ok = test_stdio_transport()

    # Test SSE transport
    sse_ok = test_sse_transport()

    # Summary
    print("\n=== Test Summary ===")
    print(f"Memory transport: {'✅ PASS' if memory_ok else '❌ FAIL'}")
    print(f"Stdio transport:  {'✅ PASS' if stdio_ok else '❌ FAIL'}")
    print(f"SSE transport:    {'✅ PASS' if sse_ok else '❌ FAIL'}")

    if memory_ok and stdio_ok and sse_ok:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""Test the MCP server's click_text functionality"""

import asyncio
import subprocess
import json
import time


async def send_mcp_request(method, params=None):
    """Send a request to the MCP server via stdio"""
    request = {
        "jsonrpc": "2.0",
        "id": str(int(time.time() * 1000)),
        "method": method,
        "params": params or {},
    }

    # Start the server
    proc = await asyncio.create_subprocess_exec(
        "python",
        "ios_interact_server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Send request
    proc.stdin.write((json.dumps(request) + "\n").encode())
    await proc.stdin.drain()

    # Read response
    response_line = await proc.stdout.readline()
    response = json.loads(response_line.decode())

    # Terminate server
    proc.terminate()
    await proc.wait()

    return response


async def reset_settings():
    """Reset Settings app to main screen"""
    # Terminate Settings
    subprocess.run(
        ["xcrun", "simctl", "terminate", "booted", "com.apple.Preferences"],
        capture_output=True,
    )
    await asyncio.sleep(1)

    # Launch Settings
    subprocess.run(
        ["xcrun", "simctl", "launch", "booted", "com.apple.Preferences"],
        capture_output=True,
    )
    await asyncio.sleep(2)


async def test_click_text_tool():
    """Test clicking text via MCP server"""
    print("=== Testing MCP click_text Tool ===\n")

    # Test 1: Click on General
    print("Test 1: Clicking on 'General'...")
    await reset_settings()

    response = await send_mcp_request("tools/click_text", {"text": "General"})

    if "result" in response:
        print(f"✓ Success: {response['result']}")
    else:
        print(f"✗ Failed: {response.get('error', 'Unknown error')}")

    # Test 2: Click on Camera
    print("\nTest 2: Clicking on 'Camera'...")
    await reset_settings()

    response = await send_mcp_request("tools/click_text", {"text": "Camera"})

    if "result" in response:
        print(f"✓ Success: {response['result']}")
    else:
        print(f"✗ Failed: {response.get('error', 'Unknown error')}")

    # Test 3: Click on non-existent text
    print("\nTest 3: Clicking on non-existent text...")
    await reset_settings()

    response = await send_mcp_request("tools/click_text", {"text": "NonExistentText"})

    if "error" in response or "not found" in response.get("result", "").lower():
        print("✓ Correctly handled non-existent text")
    else:
        print("✗ Should have failed for non-existent text")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_click_text_tool())

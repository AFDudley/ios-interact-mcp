#!/usr/bin/env python3
"""Debug AppleScript output"""

import asyncio


async def debug_applescript():
    script = """
    tell application "System Events"
        if exists process "Simulator" then
            tell process "Simulator"
                set windowList to {}
                repeat with w in windows
                    set windowInfo to {name of w, position of w, size of w, id of w}
                    set end of windowList to windowInfo
                end repeat
                return windowList
            end tell
        end if
        return {}
    end tell
    """

    proc = await asyncio.create_subprocess_exec(
        "osascript",
        "-e",
        script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    print(f"Return code: {proc.returncode}")
    print(f"Stdout: {stdout.decode()}")
    print(f"Stderr: {stderr.decode()}")

    # Also try a simpler script
    simple_script = """
    tell application "System Events"
        return name of every process
    end tell
    """

    proc2 = await asyncio.create_subprocess_exec(
        "osascript",
        "-e",
        simple_script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout2, stderr2 = await proc2.communicate()

    print(f"\nProcess list return code: {proc2.returncode}")
    print(f"Process list: {stdout2.decode()[:200]}...")


if __name__ == "__main__":
    asyncio.run(debug_applescript())

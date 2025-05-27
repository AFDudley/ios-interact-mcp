"""
Functional XCRun Controller for iOS Simulator interaction.

This module implements a functional programming approach to simulator control,
emphasizing immutability, pure functions, and explicit side effects.
"""

import asyncio
import re
from typing import List, Optional, Tuple
from pathlib import Path

from .interact_types import (
    SimulatorCommand,
    CommandResult,
    App,
    AppList,
)


# ============================================================================
# Pure Functions - No side effects, deterministic
# ============================================================================


def create_launch_command(
    bundle_id: str, wait_for_debugger: bool = False
) -> SimulatorCommand:
    """Create a command to launch an app."""
    args = ["launch", bundle_id]
    if wait_for_debugger:
        args.extend(["--wait-for-debugger"])
    return SimulatorCommand(command=args)


def create_terminate_command(bundle_id: str) -> SimulatorCommand:
    """Create a command to terminate an app."""
    return SimulatorCommand(command=["terminate", bundle_id])


def create_list_apps_command() -> SimulatorCommand:
    """Create a command to list all apps."""
    return SimulatorCommand(command=["listapps"])


def create_open_url_command(url: str) -> SimulatorCommand:
    """Create a command to open a URL."""
    return SimulatorCommand(command=["openurl", url])


def create_get_app_container_command(
    bundle_id: str, container_type: str = "data"
) -> SimulatorCommand:
    """Create a command to get app container path."""
    return SimulatorCommand(command=["get_app_container", bundle_id, container_type])


def parse_app_from_plist_block(
    lines: List[str], start_idx: int
) -> Optional[Tuple[App, int]]:
    """
    Parse a single app from plist output starting at given index.

    Returns the parsed App and the index after this app's block,
    or None if no valid app found.
    """

    def handle_quoted_values(line: str) -> str:
        """Extract value from plist line, handling both quoted and unquoted values."""
        if '"' in line:
            return line.split('"')[1]
        else:
            return line.split("= ", 1)[1].strip(" ;")

    if start_idx >= len(lines):
        return None

    line = lines[start_idx].strip()

    # Check if this line starts an app block
    # The line should contain a quoted bundle ID followed by =     { or = {
    if '"' not in line or "=" not in line or "{" not in line:
        return None

    # More flexible parsing for bundle ID
    parts = line.split('"')
    if len(parts) < 3:  # Need at least: prefix, bundle_id, suffix
        return None

    bundle_id = parts[1]  # The bundle ID is between the first pair of quotes

    # Verify this is actually an app block (must have = and { after the bundle ID)
    after_bundle_id = line.split('"')[-1]
    if "=" not in after_bundle_id or "{" not in after_bundle_id:
        return None

    # Parse app properties
    display_name = None
    bundle_name = None
    app_type = None

    idx = start_idx + 1
    brace_count = 1  # We've seen the opening brace

    while idx < len(lines) and brace_count > 0:
        line = lines[idx].strip()

        # Count braces to track nesting
        brace_count += line.count("{") - line.count("}")

        # Parse properties
        if "CFBundleDisplayName = " in line:
            try:
                display_name = handle_quoted_values(line)
            except IndexError:
                pass
        elif "CFBundleName = " in line:
            try:
                bundle_name = handle_quoted_values(line)
            except IndexError:
                pass
        elif "ApplicationType = " in line:
            try:
                app_type = line.split("= ", 1)[1].strip(' ";')
            except IndexError:
                pass

        idx += 1

    # Create app if we have at least a bundle ID
    if bundle_id and (display_name or bundle_name):
        app = App(
            bundle_id=bundle_id,
            display_name=display_name or bundle_name or bundle_id,
            bundle_name=bundle_name,
            app_type=app_type,
        )
        return (app, idx)

    return None


def parse_app_list(output: str) -> AppList:
    """
    Parse simctl listapps output into an AppList.

    This is a pure function that parses the property list format output
    from 'xcrun simctl listapps'.
    """
    if not output or not output.strip():
        return AppList(apps=())

    lines = output.split("\n")
    apps = []
    idx = 0

    while idx < len(lines):
        result = parse_app_from_plist_block(lines, idx)
        if result:
            app, next_idx = result
            apps.append(app)
            idx = next_idx
        else:
            idx += 1

    return AppList(apps=tuple(sorted(apps, key=lambda a: a.bundle_id)))


def format_app_list(app_list: AppList) -> str:
    """Format an AppList for display."""
    if not app_list.apps:
        return "No apps found on the simulator"

    lines = [f"Installed apps ({len(app_list.apps)}):"]
    for app in app_list.apps:
        lines.append(f"• {app.name} ({app.bundle_id})")

    return "\n".join(lines)


def parse_command_success(output: str, error: str, exit_code: int) -> bool:
    """Determine if a command succeeded based on output and exit code."""
    # Some commands return 0 even on failure, so check output
    if exit_code != 0:
        return False

    # Check for common error patterns
    error_patterns = [
        "error:",
        "Error:",
        "ERROR:",
        "failed",
        "Failed",
        "FAILED",
        "An error was encountered",
        "No devices are booted",
    ]

    combined_output = (output + error).lower()
    return not any(pattern.lower() in combined_output for pattern in error_patterns)


def extract_app_launch_pid(output: str) -> Optional[int]:
    """Extract the PID from app launch output."""
    # simctl launch output format: "com.example.app: <pid>"
    match = re.search(r": (\d+)", output)
    if match:
        return int(match.group(1))
    return None


# ============================================================================
# Async I/O Functions - Side effects isolated here
# ============================================================================


async def execute_command(command: SimulatorCommand) -> CommandResult:
    """
    Execute a simulator command. This is the ONLY function that performs I/O.

    All simulator interactions go through this single point.
    """
    cmd_args = ["xcrun", "simctl"] + command.to_args()

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        # Determine success
        success = parse_command_success(stdout, stderr, proc.returncode or 0)

        return CommandResult(
            success=success,
            output=stdout,
            error=stderr if stderr else None,
            exit_code=proc.returncode or 0,
        )

    except Exception as e:
        return CommandResult(
            success=False,
            output="",
            error=str(e),
            exit_code=-1,
        )


# ============================================================================
# High-Level Functional API - Compose pure functions with I/O
# ============================================================================


async def get_apps() -> AppList:
    """Get all installed apps on the simulator as structured data."""
    cmd = create_list_apps_command()
    result = await execute_command(cmd)

    if not result.success:
        raise RuntimeError(f"Failed to list apps: {result.error or result.output}")

    return parse_app_list(result.output)


async def list_apps() -> str:
    """List all installed apps on the simulator as formatted text."""
    app_list = await get_apps()
    return format_app_list(app_list)


async def launch_app(bundle_id: str, wait_for_debugger: bool = False) -> Optional[int]:
    """Launch an app on the simulator.

    Returns:
        The process ID of the launched app, or None if PID not available.
    """
    cmd = create_launch_command(bundle_id, wait_for_debugger)
    result = await execute_command(cmd)

    if not result.success:
        raise RuntimeError(
            f"Failed to launch {bundle_id}: {result.error or result.output}"
        )

    return extract_app_launch_pid(result.output)


async def terminate_app(bundle_id: str) -> None:
    """Terminate a running app."""
    cmd = create_terminate_command(bundle_id)
    result = await execute_command(cmd)

    if not result.success:
        # Don't raise error if app simply isn't running
        if "found nothing to terminate" in (result.error or result.output or ""):
            return  # Gracefully handle app not running

        raise RuntimeError(
            f"Failed to terminate {bundle_id}: {result.error or result.output}"
        )


async def open_url(url: str) -> None:
    """Open a URL in the simulator."""
    cmd = create_open_url_command(url)
    result = await execute_command(cmd)

    if not result.success:
        raise RuntimeError(f"Failed to open URL {url}: {result.error or result.output}")


async def get_app_container(bundle_id: str, container_type: str = "data") -> Path:
    """Get the app container path.

    Returns:
        Path to the app container directory.
    """
    cmd = create_get_app_container_command(bundle_id, container_type)
    result = await execute_command(cmd)

    if not result.success:
        raise RuntimeError(
            f"Failed to get {container_type} container for {bundle_id}: "
            f"{result.error or result.output}"
        )

    container_path = result.output.strip()
    if not container_path:
        raise RuntimeError(f"Empty container path returned for {bundle_id}")

    return Path(container_path)


async def press_button(button_name: str) -> None:
    """
    Press a hardware button on the simulator.

    Note: This uses a different approach since 'simctl io button' doesn't exist.
    We'll need to use device-specific commands or return a helpful message.
    """
    # For now, raise an error indicating the limitation
    # In the future, this could use AppleScript or other methods
    raise NotImplementedError(
        f"Button press for '{button_name}' is not directly supported by simctl. "
        "Consider using keyboard shortcuts or UI automation instead."
    )


# ============================================================================
# Advanced Functional Compositions
# ============================================================================


async def find_and_launch_app(app_name: str) -> Optional[int]:
    """Find an app by name and launch it.

    Returns:
        The process ID of the launched app, or None if PID not available.
    """
    # Get app list
    app_list = await get_apps()

    # Find app
    app = app_list.find_by_name(app_name)

    if not app:
        # Try partial match
        app_name_lower = app_name.lower()
        app = next((a for a in app_list.apps if app_name_lower in a.name.lower()), None)

    if not app:
        available_apps = "\n".join(f"• {a.name} ({a.bundle_id})" for a in app_list.apps)
        raise ValueError(
            f"App '{app_name}' not found. Available apps:\n{available_apps}"
        )

    # Launch the app
    return await launch_app(app.bundle_id)


async def launch_app_and_wait(bundle_id: str, wait_time: float = 2.0) -> Optional[int]:
    """Launch an app and wait for it to start.

    Returns:
        The process ID of the launched app, or None if PID not available.
    """
    pid = await launch_app(bundle_id)
    await asyncio.sleep(wait_time)
    return pid

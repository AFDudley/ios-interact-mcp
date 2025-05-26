#!/usr/bin/env python3
"""
Controller for xcrun simctl commands.
Provides interface to iOS Simulator via xcrun simctl.
"""

import asyncio
import subprocess
from typing import Tuple


class SimulatorController:
    """Wrapper for xcrun simctl commands"""

    @staticmethod
    def run_command(args: list[str]) -> Tuple[bool, str]:
        """Run a simctl command and return success status and output"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl"] + args, capture_output=True, text=True, check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr or e.stdout or str(e)

    @staticmethod
    async def run_command_async(args: list[str]) -> Tuple[bool, str]:
        """Async version of run_command"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun",
                "simctl",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return True, stdout.decode().strip()
            else:
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                return False, error_msg
        except Exception as e:
            return False, str(e)

    @staticmethod
    async def launch_app(bundle_id: str) -> Tuple[bool, str]:
        """Launch an iOS app in the simulator"""
        success, output = await SimulatorController.run_command_async(
            ["launch", "booted", bundle_id]
        )
        if success:
            return True, f"Successfully launched {bundle_id}"
        else:
            return False, f"Failed to launch {bundle_id}: {output}"

    @staticmethod
    async def terminate_app(bundle_id: str) -> Tuple[bool, str]:
        """Terminate a running iOS app"""
        success, output = await SimulatorController.run_command_async(
            ["terminate", "booted", bundle_id]
        )
        if success:
            return True, f"Successfully terminated {bundle_id}"
        else:
            return False, f"Failed to terminate {bundle_id}: {output}"

    @staticmethod
    async def list_apps() -> Tuple[bool, str]:
        """List all installed apps on the simulator"""
        success, output = await SimulatorController.run_command_async(
            ["listapps", "booted"]
        )

        if success:
            # The output is in property list format, not JSON
            # We need to parse it differently
            apps_list = []

            # Simple parsing - look for bundle IDs and names
            lines = output.split("\n")
            current_bundle_id = None
            current_app_name = None

            for line in lines:
                line = line.strip()

                # Bundle ID line (e.g., '"com.apple.Bridge" = {')
                if line.startswith('"') and line.endswith("= {"):
                    current_bundle_id = line.split('"')[1]

                # Display name line
                elif "CFBundleDisplayName = " in line:
                    current_app_name = line.split("= ")[1].strip(' ";')

                # Bundle name line (fallback)
                elif "CFBundleName = " in line and not current_app_name:
                    current_app_name = line.split("= ")[1].strip(' ";')

                # End of app block
                elif line == "};" and current_bundle_id and current_app_name:
                    apps_list.append(f"• {current_app_name} ({current_bundle_id})")
                    current_bundle_id = None
                    current_app_name = None

            if apps_list:
                return True, f"Installed apps ({len(apps_list)}):\n" + "\n".join(
                    sorted(apps_list)
                )
            else:
                return True, "No apps found on the simulator"
        else:
            return False, f"Failed to list apps: {output}"

    @staticmethod
    async def open_url(url: str) -> Tuple[bool, str]:
        """Open a URL in the simulator (useful for deep linking)"""
        success, output = await SimulatorController.run_command_async(
            ["openurl", "booted", url]
        )
        if success:
            return True, f"Successfully opened URL: {url}"
        else:
            return False, f"Failed to open URL: {output}"

    @staticmethod
    async def get_app_container(
        bundle_id: str, container_type: str = "data"
    ) -> Tuple[bool, str]:
        """Get the app container path for file access"""
        success, output = await SimulatorController.run_command_async(
            ["get_app_container", "booted", bundle_id, container_type]
        )

        if success:
            container_path = output.strip()
            return True, f"App container path ({container_type}):\n{container_path}"
        else:
            return False, f"Failed to get app container: {output}"

    @staticmethod
    async def press_button(button_name: str) -> Tuple[bool, str]:
        """Press a hardware button on the simulator"""
        # Use case-insensitive button name
        simctl_button = button_name.lower()

        # Use proper simctl command format
        success, output = await SimulatorController.run_command_async(
            ["io", "booted", "button", simctl_button]
        )

        if success:
            return True, f"Pressed {button_name} button"
        else:
            return False, f"Failed to press button: {output}"

#!/usr/bin/env python3
"""
Controller for OCR and window management via osascript.
Provides OCR text finding and AppleScript-based window control.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ocrmac import ocrmac
from PIL import Image


class SimulatorWindowManager:
    """Manages simulator windows using osascript"""

    @staticmethod
    async def verify_fullscreen_state(expected_state: str) -> bool:
        """Verify the current fullscreen state matches expected state

        Args:
            expected_state: Either "fullscreen" or "windowed"

        Returns:
            True if state matches, False otherwise
        """
        verify_script = """
        tell application "System Events"
            tell process "Simulator"
                tell menu "Window" of menu bar 1
                    if exists menu item "Exit Full Screen" then
                        return "fullscreen"
                    else if exists menu item "Enter Full Screen" then
                        return "windowed"
                    else
                        return "unknown"
                    end if
                end tell
            end tell
        end tell
        """

        proc = await asyncio.create_subprocess_exec(
            "osascript",
            "-e",
            verify_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return False

        actual_state = stdout.decode().strip()
        return actual_state == expected_state

    @staticmethod
    async def make_window_fullscreen(window_name: Optional[str] = None) -> bool:
        """Make a simulator window fullscreen using AppleScript

        Args:
            window_name: Optional window name to target. If None, uses frontmost window.

        Returns:
            True if successful or already in fullscreen, False otherwise
        """
        # First check which menu item exists
        check_script = """
        tell application "Simulator"
            activate
        end tell
        
        delay 0.5
        
        tell application "System Events"
            tell process "Simulator"
                tell menu "Window" of menu bar 1
                    if exists menu item "Enter Full Screen" then
                        return "enter"
                    else if exists menu item "Exit Full Screen" then
                        return "exit"
                    else
                        return "none"
                    end if
                end tell
            end tell
        end tell
        """

        proc = await asyncio.create_subprocess_exec(
            "osascript",
            "-e",
            check_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Failed to check fullscreen menu state: {stderr.decode()}"
            )

        menu_state = stdout.decode().strip()

        if menu_state == "exit":
            # Already in fullscreen
            raise RuntimeError("Simulator is already in fullscreen mode")
        elif menu_state == "enter":
            # Need to enter fullscreen - use keyboard shortcut instead of menu
            enter_script = """
            tell application "System Events"
                tell process "Simulator"
                    keystroke "f" using {control down, command down}
                end tell
            end tell
            """

            proc = await asyncio.create_subprocess_exec(
                "osascript",
                "-e",
                enter_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(f"Failed to enter fullscreen: {stderr.decode()}")

            # Give it time to enter fullscreen
            await asyncio.sleep(1)

            # Verify we actually entered fullscreen
            if await SimulatorWindowManager.verify_fullscreen_state("fullscreen"):
                return True
            else:
                raise RuntimeError("Failed to enter fullscreen - verification failed")
        else:
            # Menu not found
            raise RuntimeError(
                f"Could not find fullscreen menu items. Menu state: {menu_state}"
            )

    @staticmethod
    async def exit_fullscreen() -> bool:
        """Exit fullscreen mode for the Simulator"""
        # First check if we're actually in fullscreen
        check_script = """
        tell application "Simulator"
            activate
        end tell
        
        delay 0.5
        
        tell application "System Events"
            tell process "Simulator"
                tell menu "Window" of menu bar 1
                    if exists menu item "Exit Full Screen" then
                        return "exit"
                    else if exists menu item "Enter Full Screen" then
                        return "enter"
                    else
                        return "none"
                    end if
                end tell
            end tell
        end tell
        """

        proc = await asyncio.create_subprocess_exec(
            "osascript",
            "-e",
            check_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Failed to check fullscreen menu state: {stderr.decode()}"
            )

        menu_state = stdout.decode().strip()

        if menu_state == "enter":
            # Already in windowed mode
            raise RuntimeError("Simulator is already in windowed mode")
        elif menu_state == "exit":
            # Need to exit fullscreen - use keyboard shortcut instead of menu
            exit_script = """
            tell application "System Events"
                tell process "Simulator"
                    keystroke "f" using {control down, command down}
                end tell
            end tell
            """

            proc = await asyncio.create_subprocess_exec(
                "osascript",
                "-e",
                exit_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(f"Failed to exit fullscreen: {stderr.decode()}")

            # Give it time to exit fullscreen
            await asyncio.sleep(1)

            # Verify we actually exited fullscreen
            if await SimulatorWindowManager.verify_fullscreen_state("windowed"):
                return True
            else:
                raise RuntimeError("Failed to exit fullscreen - verification failed")
        else:
            # Menu not found
            raise RuntimeError(
                f"Could not find fullscreen menu items. Menu state: {menu_state}"
            )

    @staticmethod
    async def click_at_screen_coordinates(x: int, y: int) -> bool:
        """Click at absolute screen coordinates using osascript"""
        script = f"""
        tell application "System Events"
            click at {{{x}, {y}}}
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

        # If there's no stderr and the process completed, assume success
        # osascript doesn't always return meaningful exit codes for UI actions
        return proc.returncode == 0

    @staticmethod
    async def get_simulator_windows() -> List[Dict[str, Any]]:
        """Get all simulator windows with their properties"""
        script = """
        tell application "System Events"
            if exists process "Simulator" then
                tell process "Simulator"
                    set windowList to {}
                    repeat with w in windows
                        set windowInfo to {name of w, position of w, size of w}
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

        if proc.returncode != 0:
            raise RuntimeError(f"Failed to get simulator windows: {stderr.decode()}")

        # Parse the AppleScript list output
        result = stdout.decode().strip()
        if not result or result == "{}":
            return []  # Empty result is valid - no windows open

        # Parse the nested list structure
        windows = []
        # The output format is like: iPhone 15 - iOS 17.2, 100, 50, 390, 844, 12345
        # We need to parse this carefully

        # Remove outer braces if present
        if result.startswith("{") and result.endswith("}"):
            result = result[1:-1]

        # Split by window entries (separated by }, {)
        window_strings = result.split("}, {")

        for window_str in window_strings:
            # Clean up the string
            window_str = window_str.strip("{}")

            # Parse the comma-separated values
            parts = [p.strip() for p in window_str.split(", ")]

            if len(parts) >= 5:
                windows.append(
                    {
                        "name": parts[0],
                        "position": [int(parts[1]), int(parts[2])],
                        "size": [int(parts[3]), int(parts[4])],
                        "id": None,
                    }
                )

        return windows

    @staticmethod
    async def get_simulator_windows_formatted() -> str:
        """Get all simulator windows with formatted output"""
        windows = await SimulatorWindowManager.get_simulator_windows()
        if not windows:
            return "No simulator windows found. Make sure iOS Simulator is running."

        results = [f"Found {len(windows)} simulator window(s):"]
        for i, window in enumerate(windows, 1):
            results.append(
                f"{i}. {window['name']}\n"
                f"   Position: ({window['position'][0]}, {window['position'][1]})\n"
                f"   Size: {window['size'][0]}x{window['size'][1]}\n"
                f"   ID: {window['id']}"
            )
        return "\n".join(results)

    # @staticmethod
    # async def capture_window_screenshot(
    #     window_bounds: Tuple[int, int, int, int], output_path: str
    # ) -> bool:
    #     """Capture a screenshot of a specific region using screencapture

    #     Args:
    #         window_bounds: Tuple of (x, y, width, height)
    #         output_path: Path to save the screenshot

    #     Returns:
    #         True if successful, False otherwise
    #     """
    #     x, y, width, height = window_bounds

    #     proc = await asyncio.create_subprocess_exec(
    #         "screencapture",
    #         "-R",
    #         f"{x},{y},{width},{height}",
    #         "-x",
    #         output_path,
    #         stdout=asyncio.subprocess.PIPE,
    #         stderr=asyncio.subprocess.PIPE,
    #     )
    #     stdout, stderr = await proc.communicate()

    #     return proc.returncode == 0 and Path(output_path).exists()

    @staticmethod
    async def capture_simulator_screenshot(
        device_name: Optional[str] = None, use_fullscreen: bool = True
    ) -> Optional[str]:
        """Capture a screenshot of a simulator window

        Args:
            device_name: Optional name of the device to capture. If None, captures the first window.
            use_fullscreen: Whether to make window fullscreen before capture (default: True)

        Returns:
            Path to the screenshot file if successful, None otherwise
        """
        # Make window fullscreen if requested
        if use_fullscreen:
            await SimulatorWindowManager.make_window_fullscreen(device_name)
            # After fullscreen, window should be at 0,0 with size of display
            # Get display size using a simple AppleScript
            script = """
            tell application "Finder"
                get bounds of window of desktop
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

            # Parse bounds (e.g., "0, 0, 1920, 1080")
            try:
                bounds_str = stdout.decode().strip()
                parts = [int(x.strip()) for x in bounds_str.split(",")]
                screen_width = parts[2]
                screen_height = parts[3]
            except Exception as e:
                # TODO: Implement proper screen resolution detection method
                # Consider using system_profiler or other reliable method
                raise RuntimeError(f"Failed to detect screen resolution: {e}")

            # Fullscreen window is at 0,0 with full screen size
            bounds = (0, 0, screen_width, screen_height)
        else:
            # Original logic for windowed mode
            windows = await SimulatorWindowManager.get_simulator_windows()

            if not windows:
                return None

            # Find the target window
            target_window = None
            if device_name:
                for window in windows:
                    if device_name in window["name"]:
                        target_window = window
                        break
            else:
                target_window = windows[0]  # Use first window

            if not target_window:
                return None

            bounds = (
                target_window["position"][0],
                target_window["position"][1],
                target_window["size"][0],
                target_window["size"][1],
            )

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_file.close()

        # Capture screenshot
        if use_fullscreen:
            # In fullscreen mode, capture the entire screen
            proc = await asyncio.create_subprocess_exec(
                "screencapture",
                "-x",  # no sound
                temp_file.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0 and Path(temp_file.name).exists():
                return temp_file.name
            else:
                return None
        else:
            # Windowed mode not implemented
            raise NotImplementedError("capture window unimplemented")


class OCRTextFinder:
    """Find text in screenshots using ocrmac"""

    @staticmethod
    def find_text_elements(
        screenshot_path: str, search_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find text elements in a screenshot using OCR

        Args:
            screenshot_path: Path to the screenshot file
            search_text: Optional text to search for. If None, returns all text.

        Returns:
            List of text elements with their positions
        """
        # Run OCR - returns list of tuples: (text, confidence, [x, y, width, height])
        annotations = ocrmac.OCR(screenshot_path).recognize()

        # Get image dimensions to convert normalized coordinates to pixels
        img = Image.open(screenshot_path)
        img_width, img_height = img.size

        results = []
        for ann in annotations:
            # ann is a tuple: (text, confidence, [x, y, width, height])
            # The coordinates are normalized (0-1 range)
            text, confidence, bounds = ann
            x_norm, y_norm, width_norm, height_norm = bounds

            # Convert to pixel coordinates
            # Vision uses bottom-left origin, PIL uses top-left
            x = x_norm * img_width
            y = (1 - y_norm - height_norm) * img_height
            width = width_norm * img_width
            height = height_norm * img_height

            element = {
                "text": text,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "center_x": x + width / 2,
                "center_y": y + height / 2,
                "confidence": confidence,
            }

            # Filter by search text if provided
            if search_text is None or search_text.lower() in text.lower():
                results.append(element)

        return results


class CoordinateTransformer:
    """Transform coordinates between different coordinate spaces"""

    @staticmethod
    def screenshot_to_screen_coordinates(
        screenshot_x: float,
        screenshot_y: float,
        window_info: Optional[Dict[str, Any]] = None,
        is_fullscreen: bool = True,
    ) -> Tuple[int, int]:
        """Convert screenshot coordinates to screen coordinates

        Args:
            screenshot_x: X coordinate in screenshot (pixel coordinates)
            screenshot_y: Y coordinate in screenshot (pixel coordinates)
            window_info: Window information with position and size (not needed for fullscreen)
            is_fullscreen: Whether the window is in fullscreen mode

        Returns:
            Tuple of (screen_x, screen_y) in absolute screen coordinates
        """
        if is_fullscreen:
            # In fullscreen mode, screenshot coordinates ARE screen coordinates
            # because the window is at 0,0 and fills the entire screen
            return int(screenshot_x), int(screenshot_y)
        else:
            # In windowed mode, add window position to get screen coordinates
            if not window_info:
                raise ValueError("window_info required for non-fullscreen mode")

            screen_x = int(window_info["position"][0] + screenshot_x)
            screen_y = int(window_info["position"][1] + screenshot_y)

            return screen_x, screen_y


class SimulatorInteractionController:
    """High-level controller for simulator interactions"""

    @staticmethod
    async def click_at_coordinates(
        x: int, y: int, coordinate_space: str = "screen"
    ) -> None:
        """Click at specific coordinates

        Args:
            x: X coordinate
            y: Y coordinate
            coordinate_space: Either "screen" for absolute screen coordinates or "device" for
                             device coordinates

        Raises:
            ValueError: If coordinate_space is invalid
            RuntimeError: If no simulator windows found or click fails
        """
        if coordinate_space == "screen":
            # Direct screen coordinates
            success = await SimulatorWindowManager.click_at_screen_coordinates(x, y)
            if not success:
                raise RuntimeError(f"Failed to click at screen coordinates ({x}, {y})")
        elif coordinate_space == "device":
            # Device coordinates - need to transform to screen coordinates
            windows = await SimulatorWindowManager.get_simulator_windows()
            if not windows:
                raise RuntimeError("No simulator windows found")

            # Use first window for now
            window = windows[0]

            # Convert device coordinates to screen coordinates
            # Device coordinates are already in pixel space from OCR
            screen_x, screen_y = CoordinateTransformer.screenshot_to_screen_coordinates(
                x, y, window
            )

            success = await SimulatorWindowManager.click_at_screen_coordinates(
                screen_x, screen_y
            )
            if not success:
                raise RuntimeError(f"Failed to click at device coordinates ({x}, {y})")
        else:
            raise ValueError(
                f"Invalid coordinate_space: {coordinate_space}. Use 'screen' or 'device'"
            )

    @staticmethod
    async def click_text(
        text: str, occurrence: int = 1, device_name: Optional[str] = None
    ) -> None:
        """Click on text found in the simulator using OCR

        Args:
            text: Text to search for and click on
            occurrence: Which occurrence to click (1-based index)
            device_name: Optional device name to target

        Raises:
            RuntimeError: If screenshot capture fails, text not found, or click fails
            ValueError: If occurrence is invalid
        """
        # Capture screenshot in fullscreen mode
        screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
            device_name, use_fullscreen=True
        )

        if not screenshot_path:
            raise RuntimeError(
                "Failed to capture screenshot. Make sure iOS Simulator is running."
            )

        try:
            # Find text elements
            elements = OCRTextFinder.find_text_elements(screenshot_path, text)

            if not elements:
                await SimulatorWindowManager.exit_fullscreen()
                raise RuntimeError(f"Text '{text}' not found in simulator")

            if len(elements) < occurrence:
                await SimulatorWindowManager.exit_fullscreen()
                raise ValueError(
                    f"Only found {len(elements)} occurrence(s) of '{text}', "
                    f"but requested occurrence {occurrence}"
                )

            # Get target element (occurrence is 1-based)
            target = elements[occurrence - 1]

            # Transform coordinates - in fullscreen mode, OCR coordinates ARE screen coordinates
            screen_x, screen_y = CoordinateTransformer.screenshot_to_screen_coordinates(
                target["center_x"], target["center_y"], is_fullscreen=True
            )

            # Click at the calculated coordinates
            success = await SimulatorWindowManager.click_at_screen_coordinates(
                screen_x, screen_y
            )

            # Exit fullscreen after clicking
            await SimulatorWindowManager.exit_fullscreen()

            if not success:
                raise RuntimeError(
                    f"Found '{target['text']}' at ({screen_x}, {screen_y}) but click command failed"
                )
        finally:
            # Clean up screenshot
            if Path(screenshot_path).exists():
                Path(screenshot_path).unlink()

    @staticmethod
    async def find_text_in_simulator(
        search_text: Optional[str] = None, device_name: Optional[str] = None
    ) -> str:
        """Find text in the simulator screen using OCR

        Args:
            search_text: Optional text to search for. If None, returns all visible text.
            device_name: Optional device name to target. If None, uses first simulator.

        Returns:
            String with formatted results

        Raises:
            RuntimeError: If screenshot capture fails
        """
        # Capture screenshot in fullscreen mode
        screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
            device_name, use_fullscreen=True
        )

        if not screenshot_path:
            raise RuntimeError(
                "Failed to capture screenshot. Make sure iOS Simulator is running."
            )

        try:
            # Find text elements
            # Handle empty string as None for search
            actual_search_text = search_text if search_text else None
            elements = OCRTextFinder.find_text_elements(
                screenshot_path, actual_search_text
            )

            # Exit fullscreen after OCR
            await SimulatorWindowManager.exit_fullscreen()

            if not elements:
                if search_text:
                    return f"Text '{search_text}' not found in simulator"
                else:
                    return "No text found in simulator"

            # Format results
            if search_text:
                results = [f"Found {len(elements)} occurrence(s) of '{search_text}':"]
            else:
                results = [f"Found {len(elements)} text element(s):"]

            for i, elem in enumerate(elements, 1):
                # Coordinates are already in pixel space from OCR
                results.append(
                    f"{i}. '{elem['text']}' at ({elem['center_x']:.0f}, {elem['center_y']:.0f})"
                )

            return "\n".join(results)
        finally:
            # Clean up screenshot
            if Path(screenshot_path).exists():
                Path(screenshot_path).unlink()

    @staticmethod
    async def save_screenshot(
        filename: Optional[str] = None, return_path: bool = True
    ) -> str:
        """Take and save a screenshot of the iOS simulator

        Args:
            filename: Optional filename. If not provided, generates timestamp-based name.
                     If relative path, saves to Desktop. If absolute path, uses as-is.
            return_path: Whether to return the file path in the response

        Returns:
            Success message with optional file path

        Raises:
            OSError: If directory creation fails
            RuntimeError: If screenshot capture fails
        """
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
            raise OSError(f"Failed to create directory {directory}: {e}")

        # Verify we can write to the location
        if not os.access(directory, os.W_OK):
            raise OSError(f"Cannot write to directory: {directory}")

        # Use OCR capture method in fullscreen
        temp_screenshot = await SimulatorWindowManager.capture_simulator_screenshot(
            use_fullscreen=True
        )

        if not temp_screenshot:
            raise RuntimeError(
                "Failed to capture screenshot. Make sure iOS Simulator is running."
            )

        try:
            # Copy temp screenshot to desired location
            shutil.copy2(temp_screenshot, filename)

            # Exit fullscreen after capture
            await SimulatorWindowManager.exit_fullscreen()

            # Verify the file was created
            if os.path.exists(filename):
                if return_path:
                    return f"Screenshot saved to: {filename}"
                else:
                    return "Screenshot captured successfully"
            else:
                raise RuntimeError(f"Failed to save screenshot to: {filename}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_screenshot):
                os.unlink(temp_screenshot)

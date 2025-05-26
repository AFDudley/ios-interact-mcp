"""Tests for error handling in ocr_controller_functional."""

import pytest
from pathlib import Path
import sys
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import (
    click_text_in_simulator,
    click_at_coordinates,
    find_text_in_simulator,
    save_screenshot,
    toggle_fullscreen,
    perform_ocr,
    execute_screenshot,
)
from ios_interact_mcp.types import Window, Rectangle, ScreenshotAction


class TestErrorHandling:
    """Test error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_click_text_no_windows(self):
        """Test clicking text with no simulator windows."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout=""),  # No windows
                MagicMock(stdout=""),  # No fullscreen state
            ]

            with pytest.raises(RuntimeError, match="No simulator windows found"):
                await click_text_in_simulator("General")

    @pytest.mark.asyncio
    async def test_click_text_occurrence_out_of_range(self):
        """Test clicking text with occurrence greater than matches."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout="1, 0, 0, 390, 844, iPhone"),
                MagicMock(stdout="Enter Full Screen"),
            ]

            # Mock screenshot and OCR to return only 2 matches
            with patch("ios_interact_mcp.ocr_controller_functional.execute_screenshot"):
                mock_matches = [
                    MagicMock(text="Settings", bounds=MagicMock()),
                    MagicMock(text="Settings", bounds=MagicMock()),
                ]
                with patch(
                    "ios_interact_mcp.ocr_controller_functional.perform_ocr",
                    return_value=mock_matches,
                ):
                    with pytest.raises(ValueError, match="Only 2 occurrences"):
                        await click_text_in_simulator("Settings", occurrence=3)

    @pytest.mark.asyncio
    async def test_device_coordinates_no_windows(self):
        """Test device coordinates with no active window."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout=""),  # No windows
                MagicMock(stdout=""),
            ]

            with pytest.raises(RuntimeError, match="No simulator windows found"):
                await click_at_coordinates(100, 200, "device")

    @pytest.mark.asyncio
    async def test_screenshot_failed_process(self):
        """Test screenshot when screencapture fails."""
        window = Window(1, Rectangle(0, 0, 390, 844), "Test")
        action = ScreenshotAction(window=window, output_path=Path("/tmp/test.png"))

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"Permission denied")
            mock_proc.returncode = 1
            mock_create.return_value = mock_proc

            with pytest.raises(RuntimeError, match="Screenshot failed"):
                await execute_screenshot(action)

    @pytest.mark.asyncio
    async def test_screenshot_file_not_created(self):
        """Test screenshot when file is not created."""
        window = Window(1, Rectangle(0, 0, 390, 844), "Test")
        action = ScreenshotAction(window=window, output_path=Path("/tmp/test.png"))

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"")
            mock_proc.returncode = 0
            mock_create.return_value = mock_proc

            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(RuntimeError, match="Screenshot file not created"):
                    await execute_screenshot(action)

    @pytest.mark.asyncio
    async def test_toggle_fullscreen_verification_failed(self):
        """Test fullscreen toggle when verification fails."""
        call_count = 0

        async def mock_osascript(script, *args):
            nonlocal call_count
            call_count += 1

            if call_count in [1, 4]:  # Window enumeration
                return MagicMock(stdout="1, 0, 0, 390, 844, iPhone")
            elif call_count in [2, 5]:  # Fullscreen check
                # Both times return not fullscreen (failed to change)
                return MagicMock(stdout="Enter Full Screen")
            else:
                # Keyboard action
                return MagicMock()

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript",
            side_effect=mock_osascript,
        ):
            with patch(
                "ios_interact_mcp.ocr_controller_functional.load_applescript",
                return_value="script",
            ):
                with patch("asyncio.sleep"):
                    with pytest.raises(
                        RuntimeError, match="Failed to enter fullscreen"
                    ):
                        await toggle_fullscreen(True)

    def test_perform_ocr_invalid_image(self):
        """Test OCR with non-existent image."""
        with pytest.raises(Exception):  # ocrmac will raise some exception
            perform_ocr(Path("/nonexistent/image.png"))

    @pytest.mark.asyncio
    async def test_find_text_with_device_name(self):
        """Test finding text with specific device name."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(
                    stdout="1, 0, 0, 390, 844, iPhone 14\n2, 400, 0, 390, 844, iPhone 15"
                ),
                MagicMock(stdout="Enter Full Screen"),
            ]

            with patch("ios_interact_mcp.ocr_controller_functional.execute_screenshot"):
                with patch(
                    "ios_interact_mcp.ocr_controller_functional.perform_ocr",
                    return_value=[],
                ):
                    result = await find_text_in_simulator(device_name="iPhone 15")

                    # Should have selected the second window
                    assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_save_screenshot_with_device_not_found(self):
        """Test screenshot with device name that doesn't match."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout="1, 0, 0, 390, 844, iPhone 14"),
                MagicMock(stdout="Enter Full Screen"),
            ]

            # Device name doesn't match, should use first window
            with patch("ios_interact_mcp.ocr_controller_functional.execute_screenshot"):
                await save_screenshot("/tmp/test.png", device_name="iPhone 99")

    def test_load_applescript_not_found(self):
        """Test loading non-existent AppleScript."""
        from ios_interact_mcp.ocr_controller_functional import load_applescript

        with pytest.raises(FileNotFoundError):
            load_applescript("nonexistent_script.applescript")

    @pytest.mark.asyncio
    async def test_osascript_with_file_fallback(self):
        """Test osascript execution with file that doesn't exist."""
        from ios_interact_mcp.ocr_controller_functional import execute_osascript

        with patch("pathlib.Path.exists", return_value=False):
            with patch("asyncio.create_subprocess_exec") as mock_create:
                mock_proc = AsyncMock()
                mock_proc.communicate.return_value = (b"OK", b"")
                mock_proc.returncode = 0
                mock_create.return_value = mock_proc

                # Should fall back to inline script
                result = await execute_osascript("some_script.applescript")
                assert result.stdout == "OK"

                # Should have used -e flag for inline
                call_args = mock_create.call_args[0]
                assert "-e" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for async functions with mocked AppleScript execution."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import (
    observe_windows,
    observe_fullscreen_state,
    observe_simulator,
    execute_osascript,
    execute_click,
    execute_keyboard,
    execute_screenshot,
    click_text_in_simulator,
    click_at_coordinates,
    find_text_in_simulator,
    toggle_fullscreen,
    save_screenshot,
)
from ios_interact_mcp.types import (
    Window,
    Rectangle,
    ClickAction,
    KeyboardAction,
    ScreenshotAction,
    Point,
)


class TestAsyncFunctions:
    """Test async observation and effect functions."""

    @pytest.mark.asyncio
    async def test_observe_windows(self):
        """Test window observation with mocked osascript."""
        mock_output = "1, 100, 200, 390, 844, iPhone 14"

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.return_value = MagicMock(stdout=mock_output)

            windows = await observe_windows()

            assert len(windows) == 1
            assert windows[0].title == "iPhone 14"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_observe_fullscreen_state_true(self):
        """Test fullscreen state observation - fullscreen mode."""
        mock_output = "Exit Full Screen\nWindow"

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.return_value = MagicMock(stdout=mock_output)

            is_fullscreen = await observe_fullscreen_state()

            assert is_fullscreen is True  # Exit Full Screen means we're IN fullscreen

    @pytest.mark.asyncio
    async def test_observe_fullscreen_state_error(self):
        """Test fullscreen state observation with error."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = RuntimeError("Script failed")

            is_fullscreen = await observe_fullscreen_state()

            # Should return False on error
            assert is_fullscreen is False

    @pytest.mark.asyncio
    async def test_observe_simulator(self):
        """Test complete simulator observation."""
        mock_windows = "1, 0, 0, 390, 844, iPhone 14"
        mock_menu = "Enter Full Screen"

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout=mock_windows),
                MagicMock(stdout=mock_menu),
            ]

            observation = await observe_simulator()

            assert len(observation.windows) == 1
            assert (
                observation.is_fullscreen is False
            )  # Enter Full Screen means NOT in fullscreen
            assert observation.active_window is not None
            assert observation.timestamp > 0

    @pytest.mark.asyncio
    async def test_execute_osascript_success(self):
        """Test AppleScript execution success."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"Success", b"")
            mock_proc.returncode = 0
            mock_create.return_value = mock_proc

            result = await execute_osascript("test script")

            assert result.returncode == 0
            assert result.stdout == "Success"

    @pytest.mark.asyncio
    async def test_execute_osascript_failure(self):
        """Test AppleScript execution failure."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"Error occurred")
            mock_proc.returncode = 1
            mock_create.return_value = mock_proc

            with pytest.raises(RuntimeError, match="osascript failed"):
                await execute_osascript("test script")

    @pytest.mark.asyncio
    async def test_execute_click(self):
        """Test click action execution."""
        action = ClickAction(screen_point=Point(x=100, y=200), description="Test click")

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.return_value = MagicMock()

            await execute_click(action)

            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            assert "click_at_coordinates.applescript" in args[0]
            assert "100" in args
            assert "200" in args

    @pytest.mark.asyncio
    async def test_execute_keyboard(self):
        """Test keyboard action execution."""
        action = KeyboardAction(key_combo="cmd+q", description="Quit app")

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.return_value = MagicMock()

            await execute_keyboard(action)

            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            assert "send_keystroke.applescript" in args[0]
            assert "cmd+q" in args

    @pytest.mark.asyncio
    async def test_execute_screenshot_success(self):
        """Test screenshot execution success."""
        window = Window(1, Rectangle(0, 0, 390, 844), "Test")
        action = ScreenshotAction(window=window, output_path=Path("/tmp/test.png"))

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"")
            mock_proc.returncode = 0
            mock_create.return_value = mock_proc

            with patch("pathlib.Path.exists", return_value=True):
                screenshot = await execute_screenshot(action)

                assert screenshot.path == action.output_path
                assert screenshot.bounds == window.bounds

    @pytest.mark.asyncio
    async def test_click_at_coordinates_screen(self):
        """Test clicking at screen coordinates."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.return_value = MagicMock()

            await click_at_coordinates(100, 200, "screen")

            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_at_coordinates_device(self):
        """Test clicking at device coordinates."""
        mock_windows = "1, 1000, 100, 390, 844, iPhone"

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout=mock_windows),  # observe_windows
                MagicMock(stdout="Enter Full Screen"),  # observe_fullscreen
                MagicMock(),  # execute_click
            ]

            await click_at_coordinates(100, 200, "device")

            # Should have called execute_osascript 3 times
            assert mock_exec.call_count == 3

    @pytest.mark.asyncio
    async def test_click_at_coordinates_invalid_space(self):
        """Test clicking with invalid coordinate space."""
        with pytest.raises(ValueError, match="Invalid coordinate_space"):
            await click_at_coordinates(100, 200, "invalid")

    @pytest.mark.asyncio
    async def test_toggle_fullscreen_enter(self):
        """Test entering fullscreen mode."""
        call_count = 0

        async def mock_osascript(script, *args):
            nonlocal call_count
            call_count += 1

            if "enumerate_windows" in script or call_count in [1, 4]:
                return MagicMock(stdout="1, 0, 0, 390, 844, iPhone")
            elif "check_fullscreen" in script or call_count in [2, 5]:
                # First check: not fullscreen, second check: fullscreen
                if call_count == 2:
                    return MagicMock(stdout="Enter Full Screen")
                else:
                    return MagicMock(stdout="Exit Full Screen")
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
                    await toggle_fullscreen(True)

                    # Should have made 5 calls total
                    assert call_count == 5

    @pytest.mark.asyncio
    async def test_toggle_fullscreen_already_in_state(self):
        """Test toggling when already in target state."""
        call_count = 0

        async def mock_osascript(script, *args):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return MagicMock(stdout="1, 0, 0, 390, 844, iPhone")
            else:
                return MagicMock(stdout="Exit Full Screen")  # Already fullscreen

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript",
            side_effect=mock_osascript,
        ):
            with patch(
                "ios_interact_mcp.ocr_controller_functional.load_applescript",
                return_value="script",
            ):
                await toggle_fullscreen(True)

                # Should not execute keyboard action
                assert call_count == 2

    @pytest.mark.asyncio
    async def test_save_screenshot_no_windows(self):
        """Test screenshot with no windows."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout=""),  # No windows
                MagicMock(stdout="Enter Full Screen"),
            ]

            with pytest.raises(RuntimeError, match="No simulator windows"):
                await save_screenshot("/tmp/test.png")

    @pytest.mark.asyncio
    async def test_click_text_not_found(self):
        """Test clicking text that doesn't exist."""
        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout="1, 0, 0, 390, 844, iPhone"),
                MagicMock(stdout="Enter Full Screen"),
            ]

            with patch("ios_interact_mcp.ocr_controller_functional.execute_screenshot"):
                with patch(
                    "ios_interact_mcp.ocr_controller_functional.perform_ocr",
                    return_value=[],
                ):
                    with pytest.raises(ValueError, match="Text .* not found"):
                        await click_text_in_simulator("NonExistent")

    @pytest.mark.asyncio
    async def test_find_text_cleanup(self):
        """Test that find_text cleans up temporary files."""
        import tempfile

        temp_path = None

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            mock_exec.side_effect = [
                MagicMock(stdout="1, 0, 0, 390, 844, iPhone"),
                MagicMock(stdout="Enter Full Screen"),
            ]

            with patch(
                "ios_interact_mcp.ocr_controller_functional.execute_screenshot"
            ) as mock_screenshot:
                # Capture the temp file path
                original_tempfile = tempfile.NamedTemporaryFile

                def capture_temp(*args, **kwargs):
                    nonlocal temp_path
                    tmp = original_tempfile(*args, **kwargs)
                    temp_path = Path(tmp.name)
                    return tmp

                with patch("tempfile.NamedTemporaryFile", side_effect=capture_temp):
                    with patch(
                        "ios_interact_mcp.ocr_controller_functional.perform_ocr",
                        return_value=[],
                    ):
                        result = await find_text_in_simulator("test")

                        # File should be cleaned up
                        assert temp_path is not None
                        assert not temp_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

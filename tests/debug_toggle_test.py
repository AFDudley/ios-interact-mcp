"""Debug toggle fullscreen test."""

import asyncio
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.ocr_controller_functional import toggle_fullscreen


async def test_toggle():
    """Test toggle fullscreen to see actual call pattern."""
    with patch(
        "ios_interact_mcp.ocr_controller_functional.load_applescript"
    ) as mock_load:
        # Mock the script loading
        mock_load.side_effect = [
            "enumerate windows script",
            "check fullscreen script",
            "enumerate windows script",
            "check fullscreen script",
        ]

        with patch(
            "ios_interact_mcp.ocr_controller_functional.execute_osascript"
        ) as mock_exec:
            with patch("asyncio.sleep"):
                # Track all calls
                calls = []

                def track_call(*args, **kwargs):
                    calls.append(args)
                    if "enumerate" in str(args):
                        return MagicMock(stdout="1, 0, 0, 390, 844, iPhone")
                    elif "check" in str(args):
                        # First time not fullscreen, second time fullscreen
                        if len([c for c in calls if "check" in str(c)]) == 1:
                            return MagicMock(stdout="Enter Full Screen")
                        else:
                            return MagicMock(stdout="Exit Full Screen")
                    else:
                        return MagicMock()

                mock_exec.side_effect = track_call

                await toggle_fullscreen(True)

                print(f"Total calls: {len(calls)}")
                for i, call in enumerate(calls):
                    print(f"Call {i}: {call}")


asyncio.run(test_toggle())

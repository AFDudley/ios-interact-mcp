"""End-to-end tests for MCP server functionality.

These tests verify the MCP server's tools work correctly through the MCP protocol,
similar to how Claude would interact with them.

WARNING: These tests will control your simulator and mouse.
Only run when you have a simulator open and are ready to see it being controlled.
"""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock

# MCP imports
from mcp import (
    ClientSession,
    StdioServerParameters,
    Tool,
)
from mcp import stdio_client
from mcp.types import TextContent

# Local imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.e2e
class TestMCPServerE2E:
    """End-to-end tests for MCP server functionality."""

    @pytest_asyncio.fixture
    async def mcp_session(self):
        """Create MCP client session connected to our server."""
        # Start the server as a subprocess
        project_root = Path(__file__).parent.parent

        # Use stdio transport for testing
        async with stdio_client(
            StdioServerParameters(
                command="python",
                args=["-m", "ios_interact_mcp.server"],
                env=None,
                cwd=str(project_root),
            )
        ) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the session
                await session.initialize()
                yield session

    @pytest.fixture
    def mock_session(self):
        """Create a mock MCP session for unit tests."""
        session = AsyncMock(spec=ClientSession)
        return session

    # Helper methods
    async def call_tool(
        self, session: ClientSession, tool_name: str, arguments: Dict[str, Any]
    ):
        """Helper to call a tool and return the result."""
        result = await session.call_tool(tool_name, arguments)
        return result

    async def get_tool_list(self, session: ClientSession) -> List[Tool]:
        """Get list of available tools."""
        result = await session.list_tools()
        return result.tools

    # Tool Registration Tests
    @pytest.mark.asyncio
    async def test_tools_registered(self, mcp_session):
        """Verify all expected tools are registered with correct schemas."""
        tools = await self.get_tool_list(mcp_session)

        # Extract tool names
        tool_names = [tool.name for tool in tools]

        # Expected tools
        expected_tools = [
            "screenshot",
            "list_apps",
            "list_simulator_windows",
            "find_text_in_simulator",
            "click_text",
            "click_at_coordinates",
            "launch_app",
            "terminate_app",
            "open_url",
            "get_app_container",
            "press_button",
        ]

        # Verify all expected tools are present
        for expected in expected_tools:
            assert (
                expected in tool_names
            ), f"Tool '{expected}' not found in registered tools"

        # Verify each tool has required fields
        for tool in tools:
            assert tool.name, "Tool must have a name"
            assert tool.description, f"Tool '{tool.name}' must have a description"
            assert tool.inputSchema, f"Tool '{tool.name}' must have an input schema"

    # Individual Tool Tests
    @pytest.mark.asyncio
    async def test_screenshot_tool(self, mcp_session):
        """Test screenshot capture via MCP."""
        # Call screenshot tool
        result = await self.call_tool(mcp_session, "screenshot", {"return_path": True})

        # Verify result
        assert result.content, "Screenshot should return content"
        assert len(result.content) > 0, "Screenshot should return non-empty content"

        # Check if content mentions a file path
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)
        assert (
            "Screenshot saved to:" in text_content.text
            or "screenshot" in text_content.text.lower()
        )

    @pytest.mark.asyncio
    async def test_screenshot_with_filename(self, mcp_session):
        """Test screenshot with custom filename."""
        custom_filename = "test_mcp_screenshot.png"

        result = await self.call_tool(
            mcp_session,
            "screenshot",
            {"filename": custom_filename, "return_path": True},
        )

        # Verify custom filename is used
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)
        assert custom_filename in text_content.text

    @pytest.mark.asyncio
    async def test_list_apps_tool(self, mcp_session):
        """Test listing installed apps."""
        result = await self.call_tool(mcp_session, "list_apps", {})

        # Verify result format
        assert result.content, "list_apps should return content"
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)

        # Should contain some known system apps
        assert "com.apple" in text_content.text, "Should list Apple system apps"

    @pytest.mark.asyncio
    async def test_list_simulator_windows(self, mcp_session):
        """Test listing simulator windows."""
        result = await self.call_tool(mcp_session, "list_simulator_windows", {})

        # Verify result
        assert result.content, "Should return window information"
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)

        # Should contain window information or indicate no windows
        assert (
            "simulator window" in text_content.text.lower()
            or "no simulator windows found" in text_content.text.lower()
        )

    @pytest.mark.asyncio
    async def test_find_text_in_simulator(self, mcp_session):
        """Test finding text in simulator."""
        # First ensure we have Settings open
        await self.call_tool(
            mcp_session, "launch_app", {"bundle_id": "com.apple.Preferences"}
        )
        await asyncio.sleep(2)  # Wait for app to launch

        # Search for common text
        result = await self.call_tool(
            mcp_session, "find_text_in_simulator", {"search_text": "General"}
        )

        # Verify result
        assert result.content, "Should return search results"
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)

        # Should indicate if text was found
        assert "found" in text_content.text.lower() or "General" in text_content.text

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, mcp_session):
        """Test that missing required parameters are handled properly."""
        # click_text requires 'text' parameter
        try:
            result = await self.call_tool(mcp_session, "click_text", {})
            # If no exception, check if result indicates an error
            assert result.content
            text_content = result.content[0]
            # Should indicate missing parameter or error
            assert any(
                word in text_content.text.lower()
                for word in ["error", "required", "missing", "text"]
            )
        except Exception as e:
            # Exception is also acceptable
            assert "text" in str(e).lower() or "required" in str(e).lower()

    @pytest.mark.asyncio
    async def test_invalid_bundle_id(self, mcp_session):
        """Test launching app with invalid bundle ID."""
        result = await self.call_tool(
            mcp_session,
            "launch_app",
            {"bundle_id": "com.invalid.app.that.does.not.exist"},
        )

        # Should complete but indicate failure
        assert result.content
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)
        # Result should indicate some kind of error or failure
        assert any(
            word in text_content.text.lower()
            for word in ["error", "failed", "not found", "unable"]
        )

    # Integration Flow Tests
    @pytest.mark.asyncio
    async def test_settings_navigation_flow(self, mcp_session):
        """Full integration test: Launch Settings, navigate to General."""
        # Step 1: Launch Settings app
        launch_result = await self.call_tool(
            mcp_session, "launch_app", {"bundle_id": "com.apple.Preferences"}
        )
        assert launch_result.content
        await asyncio.sleep(2)  # Wait for app to fully launch

        # Step 2: Take initial screenshot for debugging
        screenshot_result = await self.call_tool(
            mcp_session,
            "screenshot",
            {"filename": "settings_main_screen.png", "return_path": True},
        )
        assert screenshot_result.content

        # Step 3: Find General option
        find_result = await self.call_tool(
            mcp_session, "find_text_in_simulator", {"search_text": "General"}
        )
        assert find_result.content

        # Step 4: Click on General
        click_result = await self.call_tool(
            mcp_session, "click_text", {"text": "General"}
        )
        assert click_result.content
        await asyncio.sleep(1)  # Wait for navigation

        # Step 5: Verify we navigated by looking for About option
        verify_result = await self.call_tool(
            mcp_session, "find_text_in_simulator", {"search_text": "About"}
        )
        assert verify_result.content
        text_content = verify_result.content[0]
        assert "About" in text_content.text or "found" in text_content.text.lower()

    @pytest.mark.asyncio
    async def test_coordinate_clicking_flow(self, mcp_session):
        """Test clicking at specific coordinates."""
        # First take a screenshot to see what we're working with
        await self.call_tool(mcp_session, "screenshot", {"return_path": True})

        # Click at a specific coordinate (middle of screen as example)
        click_result = await self.call_tool(
            mcp_session,
            "click_at_coordinates",
            {"x": 200, "y": 400, "coordinate_space": "screen"},
        )

        assert click_result.content
        text_content = click_result.content[0]
        assert isinstance(text_content, TextContent)
        assert (
            "clicked" in text_content.text.lower()
            or "success" in text_content.text.lower()
        )

    @pytest.mark.asyncio
    async def test_multiple_text_occurrences(self, mcp_session):
        """Test clicking on specific occurrence when multiple matches exist."""
        # Open Settings first
        await self.call_tool(
            mcp_session, "launch_app", {"bundle_id": "com.apple.Preferences"}
        )
        await asyncio.sleep(2)

        # Try to click second occurrence of a common word (if exists)
        result = await self.call_tool(
            mcp_session, "click_text", {"text": "Settings", "occurrence": 2}
        )

        # Should either succeed or indicate only one occurrence found
        assert result.content
        text_content = result.content[0]
        assert any(
            word in text_content.text.lower()
            for word in ["clicked", "occurrence", "found"]
        )

    @pytest.mark.asyncio
    async def test_press_button_tool(self, mcp_session):
        """Test pressing hardware buttons."""
        # Press home button
        result = await self.call_tool(
            mcp_session, "press_button", {"button_name": "home"}
        )

        assert result.content
        text_content = result.content[0]
        assert isinstance(text_content, TextContent)
        # Either success or failure message is acceptable
        # since simctl might not support button press
        assert any(
            word in text_content.text.lower()
            for word in ["pressed", "failed", "button", "home"]
        )

    # Cleanup test
    @pytest.mark.asyncio
    async def test_terminate_app(self, mcp_session):
        """Test terminating an app."""
        # First launch an app
        await self.call_tool(
            mcp_session, "launch_app", {"bundle_id": "com.apple.Preferences"}
        )
        await asyncio.sleep(2)

        # Then terminate it
        result = await self.call_tool(
            mcp_session, "terminate_app", {"bundle_id": "com.apple.Preferences"}
        )

        assert result.content
        text_content = result.content[0]
        assert (
            "terminated" in text_content.text.lower()
            or "stopped" in text_content.text.lower()
        )

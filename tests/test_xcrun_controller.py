"""Tests for the functional xcrun controller."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_interact_mcp.interact_types import (
    SimulatorCommand,
    App,
    AppList,
)
from ios_interact_mcp.xcrun_controller import (
    create_launch_command,
    create_terminate_command,
    create_list_apps_command,
    create_open_url_command,
    create_get_app_container_command,
    parse_app_list,
    format_app_list,
    parse_command_success,
    extract_app_launch_pid,
    parse_app_from_plist_block,
)


class TestPureFunctions:
    """Test pure functions with no side effects."""

    def test_create_launch_command(self):
        """Test creating launch commands."""
        cmd = create_launch_command("com.example.app")
        assert cmd.command == ["launch", "com.example.app"]
        assert cmd.device == "booted"

        # With debugger flag
        cmd_debug = create_launch_command("com.example.app", wait_for_debugger=True)
        assert cmd_debug.command == ["launch", "com.example.app", "--wait-for-debugger"]

    def test_create_terminate_command(self):
        """Test creating terminate commands."""
        cmd = create_terminate_command("com.example.app")
        assert cmd.command == ["terminate", "com.example.app"]
        assert cmd.device == "booted"

    def test_create_list_apps_command(self):
        """Test creating list apps command."""
        cmd = create_list_apps_command()
        assert cmd.command == ["listapps"]
        assert cmd.device == "booted"

    def test_create_open_url_command(self):
        """Test creating open URL command."""
        cmd = create_open_url_command("https://example.com")
        assert cmd.command == ["openurl", "https://example.com"]

    def test_create_get_app_container_command(self):
        """Test creating get app container command."""
        cmd = create_get_app_container_command("com.example.app")
        assert cmd.command == ["get_app_container", "com.example.app", "data"]

        # With custom container type
        cmd_app = create_get_app_container_command("com.example.app", "app")
        assert cmd_app.command == ["get_app_container", "com.example.app", "app"]

    def test_simulator_command_to_args(self):
        """Test SimulatorCommand.to_args() method."""
        # Commands where device comes after the command
        cmd = SimulatorCommand(command=["launch", "com.example.app"])
        assert cmd.to_args() == ["launch", "booted", "com.example.app"]

        # Commands where device comes after the command
        cmd = SimulatorCommand(command=["listapps"])
        assert cmd.to_args() == ["listapps", "booted"]

        # Custom device
        cmd = SimulatorCommand(command=["launch", "com.example.app"], device="12345")
        assert cmd.to_args() == ["launch", "12345", "com.example.app"]

    def test_parse_app_list_empty(self):
        """Test parsing empty app list."""
        app_list = parse_app_list("")
        assert app_list.apps == ()

        app_list = parse_app_list("   \n  ")
        assert app_list.apps == ()

    def test_parse_app_list_single_app(self):
        """Test parsing a single app."""
        output = """
    "com.apple.Safari" =     {
        ApplicationType = System;
        CFBundleDisplayName = Safari;
        CFBundleExecutable = Safari;
        CFBundleIdentifier = "com.apple.Safari";
        CFBundleName = Safari;
        CFBundleVersion = "18.4";
    };
"""
        app_list = parse_app_list(output)
        assert len(app_list.apps) == 1

        app = app_list.apps[0]
        assert app.bundle_id == "com.apple.Safari"
        assert app.display_name == "Safari"
        assert app.bundle_name == "Safari"
        assert app.app_type == "System"

    def test_parse_app_list_multiple_apps(self):
        """Test parsing multiple apps."""
        output = """
{
    "com.apple.Bridge" =     {
        ApplicationType = System;
        CFBundleDisplayName = Watch;
        CFBundleExecutable = Bridge;
        CFBundleIdentifier = "com.apple.Bridge";
        CFBundleName = Watch;
    };
    "com.apple.Maps" =     {
        ApplicationType = System;
        CFBundleDisplayName = Maps;
        CFBundleIdentifier = "com.apple.Maps";
        CFBundleName = Maps;
    };
    "com.apple.Preferences" =     {
        ApplicationType = System;
        CFBundleDisplayName = Settings;
        CFBundleIdentifier = "com.apple.Preferences";
        CFBundleName = Preferences;
    };
}
"""
        app_list = parse_app_list(output)
        assert len(app_list.apps) == 3

        # Check they're sorted by bundle ID
        bundle_ids = [app.bundle_id for app in app_list.apps]
        assert bundle_ids == [
            "com.apple.Bridge",
            "com.apple.Maps",
            "com.apple.Preferences",
        ]

        # Check display names
        names = [app.display_name for app in app_list.apps]
        assert names == ["Watch", "Maps", "Settings"]

    def test_parse_app_with_missing_display_name(self):
        """Test parsing app that only has bundle name."""
        output = """
    "com.example.app" =     {
        ApplicationType = User;
        CFBundleName = "Example App";
        CFBundleIdentifier = "com.example.app";
    };
"""
        app_list = parse_app_list(output)
        assert len(app_list.apps) == 1

        app = app_list.apps[0]
        assert app.bundle_id == "com.example.app"
        assert app.display_name == "Example App"  # Falls back to bundle name
        assert app.bundle_name == "Example App"

    def test_format_app_list_empty(self):
        """Test formatting empty app list."""
        app_list = AppList(apps=())
        formatted = format_app_list(app_list)
        assert formatted == "No apps found on the simulator"

    def test_format_app_list_with_apps(self):
        """Test formatting app list with apps."""
        apps = (
            App(bundle_id="com.apple.Safari", display_name="Safari"),
            App(bundle_id="com.apple.Maps", display_name="Maps"),
        )
        app_list = AppList(apps=apps)
        formatted = format_app_list(app_list)

        assert "Installed apps (2):" in formatted
        assert "• Safari (com.apple.Safari)" in formatted
        assert "• Maps (com.apple.Maps)" in formatted

    def test_parse_command_success(self):
        """Test parsing command success."""
        # Success cases
        assert parse_command_success("Success", "", 0) is True
        assert parse_command_success("App launched", "", 0) is True

        # Failure cases - exit code
        assert parse_command_success("", "", 1) is False

        # Failure cases - error patterns
        assert parse_command_success("Error: App not found", "", 0) is False
        assert parse_command_success("", "Failed to launch", 0) is False
        assert parse_command_success("An error was encountered", "", 0) is False

    def test_extract_app_launch_pid(self):
        """Test extracting PID from launch output."""
        assert extract_app_launch_pid("com.example.app: 12345") == 12345
        assert extract_app_launch_pid("com.apple.Safari: 999") == 999
        assert extract_app_launch_pid("No PID here") is None
        assert extract_app_launch_pid("") is None

    def test_app_list_find_methods(self):
        """Test AppList find methods."""
        apps = (
            App(bundle_id="com.apple.Safari", display_name="Safari"),
            App(bundle_id="com.apple.Maps", display_name="Maps"),
            App(bundle_id="com.example.Test", display_name="Test App"),
        )
        app_list = AppList(apps=apps)

        # Find by bundle ID
        app = app_list.find_by_bundle_id("com.apple.Safari")
        assert app is not None
        assert app.display_name == "Safari"

        app = app_list.find_by_bundle_id("com.notfound")
        assert app is None

        # Find by name (case-insensitive)
        app = app_list.find_by_name("Maps")
        assert app is not None
        assert app.bundle_id == "com.apple.Maps"

        app = app_list.find_by_name("maps")  # lowercase
        assert app is not None
        assert app.bundle_id == "com.apple.Maps"

        app = app_list.find_by_name("Test App")
        assert app is not None
        assert app.bundle_id == "com.example.Test"

    def test_app_name_property(self):
        """Test App.name property fallback."""
        # With display name
        app = App(bundle_id="com.test", display_name="Test App")
        assert app.name == "Test App"

        # Without display name, use bundle name
        app = App(bundle_id="com.test", display_name="", bundle_name="TestBundle")
        assert app.name == "TestBundle"

        # Without either, use bundle ID
        app = App(bundle_id="com.test", display_name="", bundle_name="")
        assert app.name == "com.test"

    def test_parse_app_from_plist_block(self):
        """Test parsing individual app blocks."""
        lines = [
            '    "com.apple.Safari" =     {',
            "        ApplicationType = System;",
            "        CFBundleDisplayName = Safari;",
            '        CFBundleIdentifier = "com.apple.Safari";',
            "    };",
            '    "com.apple.Maps" =     {',
        ]

        # Parse first app
        result = parse_app_from_plist_block(lines, 0)
        assert result is not None
        app, next_idx = result
        assert app.bundle_id == "com.apple.Safari"
        assert app.display_name == "Safari"
        assert next_idx == 5  # Points to the line after the closing brace

        # Try parsing from a non-app line
        result = parse_app_from_plist_block(lines, 1)
        assert result is None

        # Parse with nested braces
        lines_nested = [
            '    "com.test.app" =     {',
            "        GroupContainers = {",
            '            "group.test" = "path";',
            "        };",
            '        CFBundleDisplayName = "Test App";',
            "    };",
        ]
        result = parse_app_from_plist_block(lines_nested, 0)
        assert result is not None
        app, next_idx = result
        assert app.bundle_id == "com.test.app"
        assert app.display_name == "Test App"
        assert next_idx == 6

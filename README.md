# iOS Interact MCP Server

A Model Context Protocol (MCP) server that provides tools for controlling both iOS Simulator and real iOS devices via `xcrun simctl` and `xcrun devicectl` commands. This server enables Claude Code to interact with iOS apps on simulators and physical devices on macOS.

## Features

- Launch and terminate iOS apps on simulators and real devices
- Take screenshots of simulators and devices
- List installed apps
- Open URLs (for deep linking)
- Access app container paths
- List available simulators and connected devices
- Automatic device detection and switching
- All operations use native macOS tools (no additional dependencies beyond Python)

## Requirements

- macOS with Xcode installed
- Python 3.8 or later
- iOS Simulator running (for simulator features)
- iOS device connected via USB (for device features)
- MCP Python SDK

## Installation

1. **Install the MCP Python SDK:**
   ```bash
   pip install mcp
   ```

2. **Download the server file:**
   Save `ios_interact_server.py` to a location on your system (e.g., `~/tools/ios-interact-mcp/`)

3. **Make the server executable:**
   ```bash
   chmod +x ios_interact_server.py
   ```

4. **For simulator usage:**
   Open Xcode and start an iOS Simulator, or use:
   ```bash
   open -a Simulator
   ```

5. **For real device usage:**
   - Connect your iOS device via USB
   - Trust the computer on your device when prompted
   - Ensure developer mode is enabled on the device

## Configuration

### Running the Server

The server now uses HTTP streaming transport by default, which allows multiple clients to connect simultaneously. Start the server:

```bash
python3 ios_interact_server.py
```

The server will run on port 6274 by default. You can verify it's running by visiting http://localhost:6274/mcp in your browser.

### Claude Code Configuration

Add the server to your Claude Code configuration file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ios-interact": {
      "command": "python3",
      "args": ["/path/to/ios_interact_server.py"],
      "env": {}
    }
  }
}
```

Replace `/path/to/ios_interact_server.py` with the actual path where you saved the server file.

### HTTP Streaming Benefits

- **Multiple Connections**: Unlike stdio transport, HTTP streaming allows multiple Claude Code instances to connect simultaneously
- **Remote Access**: Can be accessed from other machines on your network
- **Better Debugging**: HTTP endpoints can be tested with curl or browser
- **Bi-directional Communication**: Server can send notifications back to clients

## Available Tools

### list_devices
List all available iOS simulators and connected devices.
- **Parameters:** None

### select_device
Select a specific device or simulator to use for subsequent operations.
- **Parameters:**
  - `device_id` (string, required): Device identifier (UDID or name)

### launch_app
Launch an iOS app on the selected device or simulator.
- **Parameters:**
  - `bundle_id` (string, required): Bundle ID of the app to launch
  - `device_id` (string, optional): Specific device to use (overrides selected device)

### terminate_app
Terminate a running iOS app.
- **Parameters:**
  - `bundle_id` (string, required): Bundle ID of the app to terminate
  - `device_id` (string, optional): Specific device to use (overrides selected device)

### screenshot
Take a screenshot of the iOS device or simulator.
- **Parameters:**
  - `filename` (string, optional): Output filename (defaults to timestamp)
  - `return_path` (boolean, optional): Return full path in response (default: true)
  - `device_id` (string, optional): Specific device to use (overrides selected device)

### list_apps
List all installed apps on the device or simulator.
- **Parameters:**
  - `device_id` (string, optional): Specific device to use (overrides selected device)

### open_url
Open a URL on the device or simulator (useful for deep linking).
- **Parameters:**
  - `url` (string, required): URL to open
  - `device_id` (string, optional): Specific device to use (overrides selected device)

### get_app_container
Get the app container path for file access.
- **Parameters:**
  - `bundle_id` (string, required): Bundle ID of the app
  - `container_type` (string, optional): Container type - "app", "data", or "groups" (default: "data")
  - `device_id` (string, optional): Specific device to use (overrides selected device)

## Usage Examples

Once configured, you can use these commands in Claude Code:

```bash
# List available devices
use ios-interact
list_devices

# Select a device
select_device device_id="iPhone-15-Pro"

# Launch an app
launch_app bundle_id="com.apple.mobilesafari"

# Take a screenshot
screenshot filename="current_screen.png"

# List all installed apps
list_apps

# Open a deep link
open_url url="myapp://section/details"

# Get app data container path
get_app_container bundle_id="com.mycompany.myapp"
```

## Troubleshooting

### "No booted devices" error
Make sure iOS Simulator is running. You can start it with:
```bash
open -a Simulator
```

### App not found errors
Verify the bundle ID is correct using:
```bash
xcrun simctl listapps booted
```

### Permission errors
Ensure the Python script has execute permissions:
```bash
chmod +x ios_interact_server.py
```

### Real device connection issues
1. Ensure the device is connected via USB
2. Trust the computer on your device
3. Enable developer mode in Settings > Privacy & Security > Developer Mode
4. Check device connection: `xcrun devicectl list devices`

### MCP connection issues
1. Check that the path in `claude_desktop_config.json` is absolute and correct
2. Verify Python 3 is installed: `python3 --version`
3. Check Claude Code logs for error messages
4. For HTTP streaming issues:
   - Verify the server is running: `curl http://localhost:6274/mcp`
   - Check if port 6274 is available: `lsof -i :6274`
   - Try a different port if needed by modifying the server code

## Extending the Server

The server is designed to be easily extensible. To add new tools:

1. Add the tool definition to the `list_tools()` function
2. Add the implementation in the `call_tool()` function
3. Use the appropriate controller method:
   - `SimulatorController.run_command_async()` for simulator commands
   - `DeviceController.run_command_async()` for real device commands

Example of adding a new tool:
```python
# In list_tools()
Tool(
    name="set_location",
    description="Set the simulator location",
    inputSchema={
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"}
        },
        "required": ["latitude", "longitude"]
    }
)

# In call_tool()
elif name == "set_location":
    lat = arguments["latitude"]
    lon = arguments["longitude"]
    success, output = await controller.run_command_async([
        "location", "booted", "set", f"{lat},{lon}"
    ])
    return [TextContent(type="text", text=f"Location set to {lat},{lon}" if success else f"Error: {output}")]
```

## License

MIT License - Feel free to modify and distribute as needed.

## Contributing

Contributions are welcome! Some ideas for enhancements:
- Add video recording support for devices and simulators
- Implement device shake/rotation commands
- Add push notification sending
- Create higher-level workflow tools
- Add UI element detection via screenshots
- Implement device pairing and trust management
- Add performance monitoring capabilities

## Support

For issues specific to:
- This MCP server: Create an issue in the repository
- MCP SDK: Visit https://github.com/modelcontextprotocol/python-sdk
- Claude Code: Visit https://support.anthropic.com
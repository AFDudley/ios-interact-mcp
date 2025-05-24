# iOS Device Interaction via MCP Server

## Project Overview
Creating a Python-based MCP (Model Context Protocol) server to control both iOS Simulator and real iOS devices from Claude Code, enabling automated testing and interaction with iOS apps.

## Key Components

### 1. MCP Server (`ios_interact_server.py`)
- Python-based server using the official MCP SDK
- Provides tools for iOS Simulator control via `xcrun simctl`
- Supports real device control via `xcrun devicectl`
- Async implementation for better performance
- No external dependencies beyond Python and macOS tools

### 2. Available Tools
- `launch_app` - Launch iOS apps by bundle ID (simulator & device)
- `terminate_app` - Stop running apps (simulator & device)
- `screenshot` - Capture screen (simulator & device)
- `list_apps` - Show installed applications (simulator & device)
- `open_url` - Open URLs (deep linking support) (simulator & device)
- `get_app_container` - Access app file system (simulator & device)
- `list_devices` - List available simulators and connected devices
- `select_device` - Switch between simulator and real devices

### 3. Configuration
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`
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

## Technical Decisions

### Why MCP Server?
- Clean, versioned API for Claude Code
- Better error handling than raw shell scripts
- Structured tool interface
- Follows Claude Code integration patterns

### Why Python?
- Native async support
- Simple subprocess handling
- Stock macOS Python 3 compatibility
- Official MCP SDK available

### Simulator vs Real Device
- Both simulators and real devices fully supported
- Simulators use `xcrun simctl` commands
- Real devices use `xcrun devicectl` commands
- Automatic detection and switching between device types
- App Store limitations on both platforms

## Challenges & Solutions

### Challenge: App Store Access
- **Problem**: Cannot download apps from App Store in Simulator
- **Solution**: Apps must be installed via Xcode, .app bundles, or built from source

### Challenge: UI Automation
- **Current**: Basic app lifecycle control
- **Future**: Consider computer vision for screenshot-based automation
- **Alternative**: Integrate with XCTest or Appium

### Challenge: Testing a-Shell
- **Solution**: Build from source (https://github.com/holzschu/a-Shell)
- URL scheme support for command execution
- File system access via app containers

## Implementation Status

### Completed ✓
- Basic MCP server structure
- Core simulator control tools
- Real device support integration
- Device detection and switching
- Comprehensive documentation
- Error handling

### Future Enhancements
- [x] Real device support (`devicectl` integration)
- [ ] Video recording capabilities
- [ ] Computer vision for UI element detection
- [ ] Higher-level workflow automation
- [ ] Push notification simulation
- [ ] Location/hardware simulation
- [ ] Device pairing and trust management
- [ ] Performance monitoring and profiling

## Usage Examples

```bash
# In Claude Code after configuration
use ios-interact

# Launch Safari
launch_app bundle_id="com.apple.mobilesafari"

# Take screenshot
screenshot filename="test_screen.png"

# Open deep link
open_url url="myapp://section/details"

# Get app data location
get_app_container bundle_id="com.example.app"
```

## Resources

- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- xcrun simctl documentation: `man xcrun-simctl`
- a-Shell repository: https://github.com/holzschu/a-Shell

## Next Steps

1. Install MCP Python SDK: `pip install mcp`
2. Save server file and configure Claude Code
3. Test with iOS Simulator
4. Connect real iOS device and test device control
5. Build a-Shell from source for testing
6. Extend server based on specific automation needs
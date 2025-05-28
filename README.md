# iOS Interact MCP Server

Control iOS simulators through the Model Context Protocol (MCP).

NOTE: This is AI Slop, there are dragons all over the place. I think the majority of the tests are fake or otherwise nonsensical, I have manually tested everything and the only bug I've found is in the complex gestures Claude made.

## Features

- **Click Actions**: Click on UI elements by text or coordinates using OCR
- **App Control**: Launch and terminate iOS applications
- **Screenshots**: Capture simulator screenshots with OCR support
- **Text Finding**: Find and interact with text elements using OCR
- **Deep Linking**: Open URLs in the simulator
- **Hardware Buttons**: Simulate hardware button presses
- **Window Management**: List and control simulator windows

## Requirements

- macOS with Xcode installed
- Python 3.10 or higher
- iOS Simulator
- MCP-compatible client (e.g., Claude Desktop)

## Installation

### Via pip

```bash
pip install ios-interact-mcp
```

### From source

```bash
git clone https://github.com/AFDudley/ios-interact-mcp.git
cd ios-interact-mcp
pip install -e .
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ios-interact": {
      "command": "ios-interact-mcp"
    }
  }
}
```

### Standalone Usage

```bash
# Run with stdio transport (default)
ios-interact-mcp

# Run with SSE transport for debugging
ios-interact-mcp --transport sse
```

### Using with Claude Code

To use the MCP server with Claude Code, you need to start it with SSE transport and then connect Claude Code to it:

1. **Start the SSE server:**
   ```bash
   # Start the server on port 8000 (default)
   ios-interact-mcp --transport sse

   # Or specify a custom port
   ios-interact-mcp --transport sse --port 37849
   ```

2. **Connect Claude Code to the server:**
   ```bash
   # Add the MCP server to Claude Code
   claude mcp add -t sse ios-interact http://localhost:8000/sse

   # Or if using a custom port
   claude mcp add -t sse ios-interact http://localhost:37849/sse
   ```

3. **Verify the connection:**
   ```bash
   # List configured MCP servers
   claude mcp list

   # Get details about the ios-interact server
   claude mcp get ios-interact
   ```

4. **Remove the server (when done):**
   ```bash
   claude mcp remove ios-interact -s local
   ```

## Available Tools

### click_text
Click on text found in the simulator using OCR.

```typescript
click_text(text: string, occurrence?: number, simulator_name?: string)
```

### click_at_coordinates
Click at specific screen coordinates.

```typescript
click_at_coordinates(x: number, y: number, coordinate_space?: "screen")
```

### launch_app
Launch an iOS application.

```typescript
launch_app(bundle_id: string)
```

### terminate_app
Terminate a running iOS application.

```typescript
terminate_app(bundle_id: string)
```

### screenshot
Take a screenshot of the simulator.

```typescript
screenshot(filename?: string, return_path?: boolean)
```

### find_text_in_simulator
Find text elements in the simulator using OCR.

```typescript
find_text_in_simulator(search_text?: string, simulator_name?: string)
```

### list_apps
List all installed applications.

```typescript
list_apps()
```

### open_url
Open a URL in the simulator (for deep linking).

```typescript
open_url(url: string)
```

### press_button
Press a hardware button.

```typescript
press_button(button_name: "home" | "lock" | "volume_up" | "volume_down")
```

### list_simulator_windows
List all simulator windows with their positions and sizes.

```typescript
list_simulator_windows()
```

## Usage Examples

### Basic Automation

```python
# Click on Settings app
await click_text("Settings")

# Navigate to General
await click_text("General")

# Take a screenshot
await screenshot("general_settings.png")
```

### App Testing

```python
# Launch your app
await launch_app("com.yourcompany.yourapp")

# Click on UI elements
await click_text("Login")

# Enter deep link
await open_url("yourapp://profile")

# Capture state
await screenshot("profile_screen.png")
```

## Permissions

For OCR functionality to work properly, you need to grant accessibility permissions:

1. Go to System Preferences > Security & Privacy > Accessibility
2. Add Terminal (or your IDE) to the allowed applications
3. Restart the application if needed

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/AFDudley/ios-interact-mcp.git
cd ios-interact-mcp

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_ocr_controller.py
```

### Code Quality

The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **Pyright** for type checking

These are automatically run on commit via pre-commit hooks.

## Troubleshooting

### OCR Not Working

1. Ensure you have granted accessibility permissions to Terminal/your IDE
2. Check that the simulator window is visible and not minimized
3. Verify ocrmac is installed: `pip install ocrmac`

### Click Actions Failing

1. Verify the simulator is in focus
2. Ensure the target text is visible on screen
3. Try using `find_text_in_simulator` first to verify OCR is working

### "No booted devices" Error

Make sure iOS Simulator is running:
```bash
open -a Simulator
```

### Permission Errors

Grant necessary permissions in System Preferences > Security & Privacy > Accessibility

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [ocrmac](https://github.com/straussmaximilian/ocrmac) for OCR functionality
- Powered by Apple's Vision framework and xcrun tools

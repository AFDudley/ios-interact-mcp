#!/bin/bash
# Install script for iOS Interact MCP Server in Claude Desktop

set -e

echo "iOS Interact MCP Server Installation Script"
echo "=========================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This tool only works on macOS"
    exit 1
fi

# Check if Xcode is installed
if ! command -v xcrun &> /dev/null; then
    echo "Error: Xcode command line tools are not installed"
    echo "Please install Xcode from the App Store or run: xcode-select --install"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Install the package
echo "Installing ios-interact-mcp..."
pip3 install ios-interact-mcp

# Get the installed command path
COMMAND_PATH=$(which ios-interact-mcp)
if [ -z "$COMMAND_PATH" ]; then
    echo "Error: ios-interact-mcp command not found after installation"
    exit 1
fi

echo "Successfully installed at: $COMMAND_PATH"

# Configure Claude Desktop
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

echo ""
echo "Configuring Claude Desktop..."

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    # Backup existing config
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "Backed up existing config to: $CONFIG_FILE.backup"
    
    # Check if ios-interact is already configured
    if grep -q "ios-interact" "$CONFIG_FILE"; then
        echo "Warning: ios-interact is already configured in Claude Desktop"
        echo "Please manually update the configuration if needed"
    else
        # Add ios-interact to existing config
        echo "Adding ios-interact to existing configuration..."
        # This is simplified - in practice you'd use jq or similar for JSON manipulation
        echo "Please add the following to your mcpServers section in $CONFIG_FILE:"
        echo ""
        echo '    "ios-interact": {'
        echo '      "command": "ios-interact-mcp"'
        echo '    }'
    fi
else
    # Create new config file
    echo "Creating new Claude Desktop configuration..."
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "ios-interact": {
      "command": "ios-interact-mcp"
    }
  }
}
EOF
    echo "Created configuration at: $CONFIG_FILE"
fi

echo ""
echo "Testing installation..."

# Test that the server can start
if ios-interact-mcp --help &> /dev/null; then
    echo "✓ Server command is working"
else
    echo "✗ Server command failed"
    exit 1
fi

# Check if simulator is available
if xcrun simctl list &> /dev/null; then
    echo "✓ iOS Simulator tools are available"
else
    echo "✗ iOS Simulator tools not found"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop"
echo "2. Open iOS Simulator: open -a Simulator"
echo "3. Use 'ios-interact' tools in Claude"
echo ""
echo "For OCR features to work, grant accessibility permissions:"
echo "System Preferences > Security & Privacy > Accessibility > Add Terminal/Claude"
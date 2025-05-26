# iOS Interact MCP Server Architecture

## Overview

The iOS Interact MCP Server provides a bridge between MCP clients (like Claude Desktop) and iOS simulators/devices on macOS. It uses native macOS tools and the Vision framework for UI automation.

## Core Components

### 1. MCP Server Layer (`server.py`)

- Built on FastMCP for easy tool definition
- Supports both stdio and SSE transports
- Handles MCP protocol communication
- Routes tool calls to appropriate controllers

### 2. OCR Controller (`ocr_controller.py`)

The OCR controller handles all vision-based interactions:

- **SimulatorWindowManager**: Manages simulator windows using AppleScript
  - Window detection and positioning
  - Fullscreen mode management
  - Screenshot capture via `screencapture`

- **OCRTextFinder**: Text detection using ocrmac
  - Processes screenshots with Apple's Vision framework
  - Handles coordinate transformation (Vision uses bottom-left origin)
  - Returns text elements with pixel coordinates

- **CoordinateTransformer**: Coordinate space conversion
  - Screenshot space to screen space transformation
  - Handles virtual display configurations
  - Manages retina display scaling

- **SimulatorInteractionController**: High-level interaction API
  - Combines OCR, clicking, and screenshot functionality
  - Handles text-based clicking with occurrence support
  - Manages coordinate-based interactions

### 3. XCRun Controller (`xcrun_controller.py`)

Handles simulator control via `xcrun simctl`:

- App lifecycle management (launch/terminate)
- Hardware button simulation
- App listing and container access
- URL opening for deep links

## Key Design Decisions

### OCR-Based Interaction

Instead of using accessibility APIs or UI testing frameworks, we use OCR for several reasons:

1. **Simplicity**: No need for app-specific test targets
2. **Universality**: Works with any app without modification
3. **Reliability**: Vision framework provides accurate text detection
4. **MCP Compatibility**: Natural fit for LLM-driven automation

### Coordinate System Handling

The Vision framework uses bottom-left origin coordinates, while most imaging libraries use top-left. We handle this with:

```python
y = (1 - y_norm - height_norm) * img_height
```

This transformation ensures accurate clicking on detected text.

### Window Management

We use AppleScript for window management because:
- Native macOS integration
- No additional dependencies
- Reliable window detection
- Support for fullscreen mode

### Transport Options

- **stdio**: Default for Claude Desktop integration
- **SSE**: Useful for debugging and development

## Data Flow

1. **MCP Client** sends tool request (e.g., `click_text`)
2. **Server** receives and validates request
3. **Controller** executes the action:
   - Takes screenshot of simulator
   - Runs OCR to find text
   - Transforms coordinates
   - Clicks using AppleScript
4. **Response** sent back through MCP protocol

## Error Handling

- Graceful degradation when simulator not found
- Clear error messages for debugging
- Fallback strategies for window detection
- Validation of all user inputs

## Security Considerations

- Requires accessibility permissions for clicking
- All operations are local (no network access)
- No storage of sensitive information
- Read-only access to app containers

## Future Enhancements

1. **Multi-simulator support**: Better handling of multiple simulators
2. **Gesture support**: Swipe, pinch, and other gestures
3. **Video recording**: Capture automation sessions
4. **Real device support**: Extend beyond simulators
5. **Performance optimization**: Caching and batching operations
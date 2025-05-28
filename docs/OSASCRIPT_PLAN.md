# osascript Integration Plan for iOS Simulator Control

## Overview
Enhance the ios-interact MCP server to use osascript for precise control of multiple iOS simulators, handling dynamic window positioning and providing direct xcrun command access.

## Key Features

### 1. Window Identification
- Use osascript to find all iOS Simulator windows via System Events
- Extract window names, positions, and sizes
- Map booted devices to their corresponding windows

### 2. Multi-Simulator Support
- Track and control multiple simulators simultaneously
- Device-to-window mapping by matching window titles
- Simulator selection mechanism for targeting specific devices

### 3. Coordinate Transformation
- Convert device coordinates to screen coordinates
- Account for window chrome (title bar, bezels)
- Handle window scaling and different device sizes
- Dynamic adjustment for moved windows

### 4. Enhanced Interaction
- Precise clicking using osascript instead of simctl
- Target specific simulators by device ID
- Fallback to simctl for basic operations
- Support for complex gestures

### 5. xcrun Command Passthrough
- Direct access to xcrun commands (simctl)
- Special handling for copy/paste operations
- Safety checks for allowed commands
- Full parameter support

### 6. Implementation Phases

**Phase 1: Core osascript Integration**
- osascript execution helpers
- Basic window finding
- Coordinate transformation

**Phase 2: Multi-Simulator Support**
- Device identification
- Window mapping
- Selection mechanism

**Phase 3: Enhanced Commands**
- xcrun passthrough
- Copy/paste operations
- Advanced gestures

**Phase 4: Robustness**
- Window movement handling
- Retry logic
- Error recovery

## Technical Approach

### Window Detection
```applescript
tell application "System Events"
    if exists process "Simulator" then
        tell process "Simulator"
            get {name, position, size} of windows
        end tell
    end if
end tell
```

### Coordinate Transformation
- Get device screen size from simctl
- Calculate window scale factor
- Apply chrome offsets
- Transform device coordinates to screen coordinates

### Device Selection
- List all booted simulators
- Show window status for each
- Allow selection by name or UDID
- Maintain active device context

## Benefits
- Precise control over multiple simulators
- No dependency on simulator focus
- Handles moving windows
- Direct access to clipboard operations
- Extensible for future automation needs
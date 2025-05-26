# ocrmac Implementation Plan for iOS Simulator Control

## Overview
Integrate ocrmac library to enable text-based UI element detection and clicking in iOS simulators using OCR and osascript.

## Architecture

### 1. Core Components

```python
# New imports
from ocrmac import ocrmac
import tempfile
from pathlib import Path

# New classes
class SimulatorWindowManager:
    """Manages simulator windows and coordinates"""
    
class OCRButtonFinder:
    """Finds UI elements using ocrmac"""
    
class CoordinateTransformer:
    """Transforms between device, screenshot, and screen coordinates"""
```

### 2. Implementation Phases

#### Phase 1: Window Management
```python
async def get_simulator_windows():
    """Get all simulator windows with their properties"""
    script = '''
    tell application "System Events"
        if exists process "Simulator" then
            tell process "Simulator"
                set windowList to {}
                repeat with w in windows
                    set windowInfo to {name of w, position of w, size of w, id of w}
                    set end of windowList to windowInfo
                end repeat
                return windowList
            end tell
        end if
        return {}
    end tell
    '''
    # Returns: [["iPhone 15 - iOS 17.2", [100, 50], [390, 844], 12345], ...]
```

#### Phase 2: Screenshot Capture
```python
async def capture_simulator_screenshot(device_id: Optional[str] = None) -> str:
    """Capture screenshot of simulator window"""
    if device_id:
        # Find specific window and use screencapture
        window = await find_window_for_device(device_id)
        x, y, w, h = window['bounds']
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        await run_command([
            'screencapture', '-R', f'{x},{y},{w},{h}',
            '-x', temp_file.name
        ])
        return temp_file.name
    else:
        # Use simctl for booted device
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        success, _ = await SimulatorController.run_command_async([
            'io', 'booted', 'screenshot', temp_file.name
        ])
        return temp_file.name if success else None
```

#### Phase 3: OCR Integration
```python
async def find_text_elements(screenshot_path: str, search_text: Optional[str] = None):
    """Find text elements in screenshot using ocrmac"""
    annotations = ocrmac.OCR(screenshot_path).recognize()
    
    results = []
    for ann in annotations:
        element = {
            'text': ann['text'],
            'bounds': (ann['x'], ann['y'], ann['width'], ann['height']),
            'center': (ann['x'] + ann['width']/2, ann['y'] + ann['height']/2),
            'confidence': ann.get('confidence', 1.0)
        }
        
        if search_text is None or search_text.lower() in ann['text'].lower():
            results.append(element)
    
    return results
```

#### Phase 4: Coordinate Transformation
```python
class CoordinateTransformer:
    def __init__(self, window_info, device_info):
        # Window position and size on screen
        self.window_x = window_info['position'][0]
        self.window_y = window_info['position'][1]
        self.window_width = window_info['size'][0]
        self.window_height = window_info['size'][1]
        
        # Device logical size
        self.device_width = device_info.get('width', 390)
        self.device_height = device_info.get('height', 844)
        
        # Chrome offsets (title bar, bezels)
        self.chrome_top = 25  # Title bar height
        
    def screenshot_to_screen(self, x, y):
        """Convert screenshot coordinates to screen coordinates"""
        # Screenshot coords are already in screen space if using screencapture
        # Just add window position
        screen_x = self.window_x + x
        screen_y = self.window_y + y
        return int(screen_x), int(screen_y)
```

#### Phase 5: Click Execution
```python
async def click_at_screen_coordinates(x: int, y: int):
    """Click at absolute screen coordinates using osascript"""
    script = f'''
    tell application "System Events"
        click at {{{x}, {y}}}
    end tell
    '''
    
    proc = await asyncio.create_subprocess_exec(
        'osascript', '-e', script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()
```

### 3. New MCP Tools

```python
@mcp.tool()
async def click_text(
    text: str, 
    occurrence: int = 1,
    device_id: Optional[str] = None
) -> str:
    """Click on text found in the simulator"""
    # 1. Capture screenshot
    screenshot = await capture_simulator_screenshot(device_id)
    
    # 2. Find text occurrences
    elements = await find_text_elements(screenshot, text)
    
    if not elements:
        return f"Text '{text}' not found"
    
    if len(elements) < occurrence:
        return f"Only found {len(elements)} occurrences of '{text}'"
    
    # 3. Get target element
    target = elements[occurrence - 1]
    
    # 4. Get window info for coordinate transformation
    if device_id:
        window_info = await get_window_for_device(device_id)
    else:
        window_info = await get_window_for_booted_device()
    
    # 5. Transform coordinates
    click_x, click_y = target['center']
    
    # 6. Click
    await click_at_screen_coordinates(click_x, click_y)
    
    return f"Clicked on '{target['text']}' at ({click_x}, {click_y})"

@mcp.tool()
async def find_ui_elements(
    search_text: Optional[str] = None,
    device_id: Optional[str] = None
) -> str:
    """Find all UI elements or search for specific text"""
    screenshot = await capture_simulator_screenshot(device_id)
    elements = await find_text_elements(screenshot, search_text)
    
    if not elements:
        return "No text elements found"
    
    results = []
    for i, elem in enumerate(elements, 1):
        results.append(
            f"{i}. '{elem['text']}' at ({elem['center'][0]:.0f}, {elem['center'][1]:.0f})"
        )
    
    return "\n".join(results)

@mcp.tool()
async def click_at_coordinates(
    x: int,
    y: int,
    coordinate_space: str = "device",
    device_id: Optional[str] = None
) -> str:
    """Click at specific coordinates (device or screen space)"""
    if coordinate_space == "screen":
        # Direct screen coordinates
        await click_at_screen_coordinates(x, y)
    else:
        # Device coordinates - need transformation
        window_info = await get_window_for_device(device_id)
        transformer = CoordinateTransformer(window_info, {})
        screen_x, screen_y = transformer.device_to_screen(x, y)
        await click_at_screen_coordinates(screen_x, screen_y)
    
    return f"Clicked at ({x}, {y}) in {coordinate_space} coordinates"
```

### 4. Dependencies Update

```toml
# pyproject.toml additions
[tool.poetry.dependencies]
ocrmac = "^0.1.0"
```

### 5. Key Benefits

1. **No simctl tap dependency** - Uses native macOS clicking
2. **Text-based interaction** - Find and click buttons by their labels
3. **Multi-simulator support** - Target specific simulators by device ID
4. **Coordinate flexibility** - Support both device and screen coordinates
5. **Visual debugging** - Can return all found text elements with positions

### 6. Usage Examples

```python
# Click on "Sign In" button
click_text text="Sign In"

# Click second occurrence of "Next"
click_text text="Next" occurrence=2

# Find all clickable elements
find_ui_elements

# Click on specific simulator
click_text text="Submit" device_id="iPhone-15-Pro"

# Click at device coordinates
click_at_coordinates x=200 y=300 coordinate_space="device"
```

### 7. Error Handling

- Window not found → Clear error message
- Text not found → List available text elements
- Multiple matches → Show all with positions
- Screenshot failure → Fallback to simctl if available

### 8. Testing Strategy

1. Test with single simulator
2. Test with multiple simulators
3. Test window movement during operation
4. Test different text sizes and fonts
5. Test partial text matching
6. Test coordinate transformation accuracy
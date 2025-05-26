# Development Guide

## Setting Up Development Environment

### Prerequisites

- macOS with Xcode installed
- Python 3.10 or higher
- iOS Simulator
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/AFDudley/ios-interact-mcp.git
cd ios-interact-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=ios_interact_mcp tests/

# Run specific test file
python -m pytest tests/test_ocr_controller.py

# Run with verbose output
python -m pytest -v tests/
```

### Code Quality

The project enforces code quality through pre-commit hooks:

1. **Black** - Code formatting
2. **Flake8** - Style guide enforcement
3. **Pyright** - Static type checking

Run manually:
```bash
# Format code
black ios_interact_mcp tests

# Check style
flake8 ios_interact_mcp tests

# Type check
pyright ios_interact_mcp
```

## Architecture Overview

### Package Structure

```
ios_interact_mcp/
├── __init__.py          # Package initialization
├── server.py            # MCP server implementation
├── ocr_controller.py    # OCR and interaction logic
└── xcrun_controller.py  # Simulator control via xcrun
```

### Key Classes

#### SimulatorWindowManager
- Manages simulator windows using AppleScript
- Handles fullscreen mode
- Captures screenshots

#### OCRTextFinder
- Wraps ocrmac for text detection
- Handles coordinate transformation
- Filters search results

#### SimulatorInteractionController
- High-level API for interactions
- Combines OCR and clicking
- Manages state

## Common Development Tasks

### Adding a New Tool

1. Define the tool in `server.py`:
```python
@mcp.tool()
async def your_new_tool(param1: str, param2: int = 0) -> str:
    """Tool description"""
    success, message = await YourController.method(param1, param2)
    return message
```

2. Implement the logic in appropriate controller
3. Add tests in `tests/`
4. Update documentation

### Debugging OCR Issues

1. Enable debug output:
```python
# In ocr_controller.py
DEBUG = True  # Set to enable debug screenshots
```

2. Check coordinate transformation:
```python
# Test with draw_general_bbox.py example
python examples/draw_general_bbox.py
```

3. Verify permissions:
   - System Preferences > Security & Privacy > Accessibility
   - Add Terminal/IDE to allowed apps

### Testing Coordinate Systems

The Vision framework uses bottom-left origin. Test with:

```python
# Correct transformation
y = (1 - y_norm - height_norm) * img_height
```

## Debugging Tips

### MCP Server Debugging

1. Run with SSE transport:
```bash
ios-interact-mcp --transport sse
```

2. Test with curl:
```bash
# List tools
curl http://localhost:3000/sse
```

### OCR Debugging

1. Save debug screenshots:
```python
# Add to OCRTextFinder.find_text_elements
img = Image.open(screenshot_path)
img.save("debug_ocr_input.png")
```

2. Print OCR results:
```python
for text, confidence, bounds in annotations:
    print(f"{text}: {bounds}")
```

### Click Debugging

1. Verify AppleScript permissions:
```bash
osascript -e 'tell application "System Events" to click at {100, 100}'
```

2. Test coordinate transformation:
```python
# Log transformed coordinates
print(f"Original: {x_norm}, {y_norm}")
print(f"Transformed: {x}, {y}")
```

## Contributing

### Code Style

- Follow PEP 8 (enforced by Black)
- Use type hints for all functions
- Write descriptive docstrings
- Keep functions focused and small

### Testing

- Write tests for new features
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external dependencies

### Documentation

- Update README for user-facing changes
- Document architectural decisions
- Include examples for new features
- Keep CHANGELOG up to date

## Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag -a v0.1.0 -m "Release version 0.1.0"`
5. Push tag: `git push origin v0.1.0`
6. Build package: `python -m build`
7. Upload to PyPI: `python -m twine upload dist/*`

## Troubleshooting Development Issues

### Import Errors

Ensure you're in the virtual environment:
```bash
source venv/bin/activate
```

### OCR Not Working

1. Check ocrmac installation:
```bash
pip show ocrmac
```

2. Verify Vision framework:
```python
import ocrmac
print(ocrmac.version)
```

### Pre-commit Failures

1. Update hooks:
```bash
pre-commit autoupdate
```

2. Run manually:
```bash
pre-commit run --all-files
```
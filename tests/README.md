# iOS Interact MCP Tests

This directory contains tests for the iOS Interact MCP server, particularly focused on the functional OCR controller.

## Test Structure

```
tests/
├── __init__.py
├── create_test_image.py      # Script to generate test images
├── test_ocr_functions.py     # Tests for OCR functionality
├── debug_ocr_format.py       # Debug script for OCR output format
└── Test images:
    ├── test_hello_world.png
    ├── test_click_me.png
    ├── test_general.png
    ├── test_multiple_settings.png
    ├── test_special_chars.png
    ├── test_numbers.png
    └── test_simulator_settings.png
```

## Running Tests

```bash
# Run all OCR tests
python -m pytest tests/test_ocr_functions.py -v

# Run specific test
python -m pytest tests/test_ocr_functions.py::TestOCRFunctions::test_perform_ocr_hello_world -v

# Generate new test images
python tests/create_test_image.py
```

## Test Coverage

### OCR Functions
- ✅ Basic OCR text detection
- ✅ OCR with search filtering
- ✅ Coordinate parsing and transformation
- ✅ Vision to PIL coordinate conversion
- ✅ Rectangle center calculation
- ✅ Simulator-like UI testing

### Next Steps for Testing
1. **Mock AppleScript tests** - Test window observation and actions
2. **Integration tests** - Test with real simulator (requires running simulator)
3. **Error handling tests** - Test all error paths
4. **Async function tests** - Test the async observation and effect functions
5. **End-to-end tests** - Full workflow from text finding to clicking
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-25

### Added
- Initial release with core MCP server functionality
- OCR-based text finding and clicking using ocrmac
- Screenshot capture with automatic window detection
- App launching and termination via xcrun simctl
- Hardware button simulation (home, lock, volume)
- Deep linking support via URL opening
- Coordinate-based clicking with screen/device space support
- Simulator window listing and management
- Support for both stdio and SSE transports

### Fixed
- OCR coordinate transformation from Vision's bottom-left to PIL's top-left origin
- Proper handling of virtual displays and fullscreen mode

### Developer
- Added pre-commit hooks with Black, Flake8, and Pyright
- Comprehensive test suite
- Type hints throughout codebase
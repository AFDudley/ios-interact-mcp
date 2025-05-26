"""Pytest configuration for ios-interact-mcp tests."""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test that controls the simulator"
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests that control the simulator",
    )


def pytest_collection_modifyitems(config, items):
    """Skip e2e tests unless --run-e2e flag is given."""
    if config.getoption("--run-e2e"):
        # Don't skip e2e tests
        return

    skip_e2e = pytest.mark.skip(reason="Need --run-e2e option to run")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)

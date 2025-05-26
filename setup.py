#!/usr/bin/env python3
"""Setup script for ios-interact-mcp"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ios-interact-mcp",
    version="0.1.0",
    author="Your Name",
    description="iOS Interact MCP Server - Control iOS simulators and devices via MCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AFDudley/ios-interact-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
        "ocrmac>=0.3.0",
    ],
    extras_require={
        "dev": [
            "black>=24.10.0",
            "flake8>=7.1.1",
            "pyright>=1.1.389",
            "pre-commit>=3.8.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ios-interact-mcp=ios_interact_mcp.server:main",
        ],
    },
)

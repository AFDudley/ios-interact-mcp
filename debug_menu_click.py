#!/usr/bin/env python3
"""Debug menu clicking"""

import subprocess
import time

# Make sure Simulator is active
subprocess.run(
    ["osascript", "-e", 'tell application "Simulator" to activate'], capture_output=True
)
time.sleep(1)

# Try clicking the Window menu first, then the item
print("Trying to click Window menu then Exit Full Screen...")
script = """
tell application "System Events"
    tell process "Simulator"
        click menu bar item "Window" of menu bar 1
        delay 0.5
        click menu item "Exit Full Screen" of menu "Window" of ¬
            menu bar item "Window" of menu bar 1
    end tell
end tell
"""
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print(f"Result: {result.returncode}")
print(f"Stderr: {result.stderr}")

# Alternative: Try using 'perform action'
print("\nTrying perform action...")
script = """
tell application "System Events"
    tell process "Simulator"
        tell menu item "Exit Full Screen" of menu "Window" of ¬
            menu bar item "Window" of menu bar 1
            perform action "AXPress"
        end tell
    end tell
end tell
"""
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print(f"Result: {result.returncode}")
print(f"Stderr: {result.stderr}")

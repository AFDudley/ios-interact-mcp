#!/usr/bin/env python3
"""Use keyboard shortcut to toggle fullscreen"""

import subprocess
import time

# Activate Simulator first
print("Activating Simulator...")
subprocess.run(
    ["osascript", "-e", 'tell application "Simulator" to activate'], capture_output=True
)
time.sleep(0.5)

# Use Control+Command+F to toggle fullscreen
print("Sending Control+Command+F...")
script = """
tell application "System Events"
    tell process "Simulator"
        key down {control, command}
        key code 3  -- 'f' key
        key up {control, command}
    end tell
end tell
"""
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print(f"Done! Return code: {result.returncode}")

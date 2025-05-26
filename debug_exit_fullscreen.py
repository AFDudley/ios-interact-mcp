#!/usr/bin/env python3
"""Debug why exit fullscreen isn't working"""

import subprocess
import time

# First, let's check if Simulator is even the active app
print("Checking frontmost app...")
script = """
tell application "System Events"
    name of first application process whose frontmost is true
end tell
"""
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print(f"Frontmost app: {result.stdout.strip()}")

# Make Simulator frontmost
print("\nActivating Simulator...")
script = """
tell application "Simulator"
    activate
end tell
"""
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
time.sleep(1)

# Check again
script = """
tell application "System Events"
    name of first application process whose frontmost is true
end tell
"""
result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print(f"Frontmost app after activate: {result.stdout.strip()}")

# Try using keyboard shortcut instead of menu
print("\nTrying keyboard shortcut for exit fullscreen (Control+Command+F)...")
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
print(f"Keyboard shortcut result: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

-- exit_fullscreen_keystroke.applescript
-- Sends Escape key to the Simulator to exit fullscreen

tell application "Simulator" to activate
delay 0.5

tell application "System Events"
    tell process "Simulator"
        set frontmost to true
        key code 53 -- Escape key
    end tell
end tell
-- send_fullscreen_keystroke.applescript
-- Sends Control+Command+F to the Simulator for fullscreen toggle

tell application "Simulator" to activate
delay 0.5

tell application "System Events"
    tell process "Simulator"
        set frontmost to true
        keystroke "f" using {control down, command down}
    end tell
end tell
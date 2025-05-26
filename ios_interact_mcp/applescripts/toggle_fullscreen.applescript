-- toggle_fullscreen.applescript
-- Toggles fullscreen mode in the Simulator using Control+Command+F

tell application "Simulator" to activate
delay 0.5

tell application "System Events"
    tell process "Simulator"
        set frontmost to true
        keystroke "f" using {control down, command down}
    end tell
end tell
-- send_keystroke.applescript
-- Sends a keystroke to the Simulator
-- Usage: osascript send_keystroke.applescript <key>

on run argv
    if (count of argv) < 1 then
        error "Usage: send_keystroke.applescript <key>"
    end if
    
    set keyToSend to item 1 of argv as string
    
    -- Activate Simulator and send keystroke
    tell application "Simulator" to activate
    delay 0.5
    
    tell application "System Events"
        tell process "Simulator"
            set frontmost to true
            keystroke keyToSend
        end tell
    end tell
end run
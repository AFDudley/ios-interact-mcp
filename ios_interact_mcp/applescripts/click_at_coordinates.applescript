-- click_at_coordinates.applescript
-- Clicks at specific screen coordinates
-- Usage: osascript click_at_coordinates.applescript <x> <y>

on run argv
    if (count of argv) < 2 then
        error "Usage: click_at_coordinates.applescript <x> <y>"
    end if
    
    set xPos to item 1 of argv as integer
    set yPos to item 2 of argv as integer
    
    tell application "System Events"
        click at {xPos, yPos}
    end tell
end run
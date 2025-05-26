-- click_green_button.applescript
-- Clicks the green maximize/fullscreen button

tell application "System Events"
    tell process "Simulator"
        set frontmost to true
        delay 0.1
        
        tell window 1
            -- The green button is button 3 (close=1, minimize=2, maximize=3)
            click button 3
        end tell
    end tell
end tell
-- setup_clean_state.applescript
-- Sets up clean simulator state: windowed mode, home screen, Settings app closed

-- First, activate Simulator
tell application "Simulator" to activate
delay 0.5

tell application "System Events"
    tell process "Simulator"
        set frontmost to true
        
        -- Press home button to go to home screen (key code 115)
        key code 115
        delay 1
        
        -- Press home button again to ensure we're on the main home screen
        key code 115
        delay 1
    end tell
    
end tell

-- Terminate the iOS Settings app using xcrun simctl (ignore if not running)
try
    do shell script "xcrun simctl terminate booted com.apple.Preferences"
on error
    -- Settings app wasn't running, which is fine
end try

-- Check if simulator is in fullscreen and toggle to windowed if needed
tell application "Simulator"
    tell application "System Events"
        tell process "Simulator"
            tell menu bar 1
                tell menu bar item "Window"
                    tell menu "Window"
                        if exists menu item "Exit Full Screen" then
                            -- We're in fullscreen, toggle to windowed
                            keystroke "f" using {control down, command down}
                            delay 2
                        end if
                    end tell
                end tell
            end tell
        end tell
    end tell
end tell

delay 0.5
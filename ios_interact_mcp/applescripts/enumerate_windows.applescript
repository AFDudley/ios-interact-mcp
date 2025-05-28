-- enumerate_windows.applescript
-- Enumerates all Simulator windows and returns their properties

tell application "System Events"
    set allWindows to ""
    set windowIndex to 1
    
    -- Only look for the main Simulator app process
    if exists (process "Simulator") then
        tell process "Simulator"
            repeat with win in windows
                try
                    set winPos to position of win
                    set winSize to size of win
                    set winTitle to name of win
                    set winX to item 1 of winPos
                    set winY to item 2 of winPos
                    set winW to item 1 of winSize
                    set winH to item 2 of winSize
                    set windowInfo to (windowIndex as string) & ", " & (winX as string) & ", " & (winY as string) & ", " & (winW as string) & ", " & (winH as string) & ", " & winTitle
                    set allWindows to allWindows & windowInfo & "\n"
                    set windowIndex to windowIndex + 1
                on error
                    -- Skip any windows that can't be accessed
                end try
            end repeat
        end tell
    end if
    
    return allWindows
end tell
-- toggle_fullscreen_menu.applescript
-- Toggles fullscreen by clicking the Window menu item

on run argv
    set targetState to "enter"
    if (count of argv) > 0 then
        set targetState to item 1 of argv as string
    end if
    
    tell application "System Events"
        tell process "Simulator"
            set frontmost to true
            delay 0.1
            
            -- Click Window menu
            tell menu bar 1
                click menu bar item "Window"
                delay 0.1
                
                -- Click appropriate menu item
                tell menu "Window"
                    if targetState is "enter" then
                        if exists menu item "Enter Full Screen" then
                            click menu item "Enter Full Screen"
                            return "Entered fullscreen"
                        else
                            return "Already in fullscreen"
                        end if
                    else
                        if exists menu item "Exit Full Screen" then
                            click menu item "Exit Full Screen"
                            return "Exited fullscreen"
                        else
                            return "Not in fullscreen"
                        end if
                    end if
                end tell
            end tell
        end tell
    end tell
end run
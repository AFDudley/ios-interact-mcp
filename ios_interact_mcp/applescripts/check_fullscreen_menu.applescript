-- check_fullscreen_menu.applescript
-- Checks the Window menu to determine if Simulator is in fullscreen mode

tell application "System Events"
    tell process "Simulator"
        if exists then
            set frontmost to true
            delay 0.1
            tell menu bar 1
                tell menu "Window"
                    return name of menu items
                end tell
            end tell
        else
            return ""
        end if
    end tell
end tell
-- open_settings_app.applescript
-- Terminates and opens the iOS Settings app using xcrun simctl

-- First terminate the Settings app if running (ignore if not running)
try
    do shell script "xcrun simctl terminate booted com.apple.Preferences"
on error
    -- Settings app wasn't running, which is fine
end try

-- Wait a moment for termination to complete
delay 0.5

-- Launch the Settings app
do shell script "xcrun simctl launch booted com.apple.Preferences"
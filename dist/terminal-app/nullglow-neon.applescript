-- Nullglow Neon for Terminal.app
-- Run it AFTER importing Nullglow Neon.terminal:
--   open Nullglow Neon.terminal && osascript nullglow-neon.applescript
--
-- The .terminal file carries the colours. This makes the profile the default
-- for new windows and sets the font, neither of which the file can do
-- reliably. Safe to re-run.

tell application "Terminal"
    set profileName to "Nullglow Neon"

    if not (exists settings set profileName) then
        error "Profile " & profileName & " not found. Open Nullglow Neon.terminal first."
    end if

    tell settings set profileName
        -- A missing font must not abort the rest, so this is guarded.
        try
            set font to "JetBrainsMonoNF-Regular"
            set font size to 14
        end try
        set number of rows to 34
        set number of columns to 120
        set title displays window size to false
        set title displays shell path to false
    end tell

    set default settings to settings set profileName
    set startup settings to settings set profileName

    -- retheme any window that is already open
    repeat with w in windows
        try
            set current settings of w to settings set profileName
        end try
    end repeat
end tell

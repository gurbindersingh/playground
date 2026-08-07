#!/usr/bin/env bash

# Reference: https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/reference/ASLR_cmds.html#//apple_ref/doc/uid/TP40000983-CH216-SW59
# Dialog icons can be stop, note, caution, a resource name or ID, or an .icns file.
# Remove "with hidden answer" to show the editable default answer as plain text.
osascript <<'APPLESCRIPT'
set dialogResult to display dialog "Enter the encryption password:" default answer "" with hidden answer buttons {"Help", "Cancel", "Continue"} default button "Continue" cancel button "Cancel" with title "Encrypt backup" with icon caution giving up after 30
return dialogResult
APPLESCRIPT

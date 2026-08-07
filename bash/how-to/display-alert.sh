#!/usr/bin/env bash

# Reference: https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/reference/ASLR_cmds.html#//apple_ref/doc/uid/TP40000983-CH216-SW59
# Alert types: informational, warning, or critical.
# An alert can have up to three buttons.
osascript <<'APPLESCRIPT'
set alertResult to display alert "Delete backup?" message "This cannot be undone." as warning buttons {"Help", "Cancel", "Delete"} default button "Delete" cancel button "Cancel" giving up after 30
return alertResult
APPLESCRIPT

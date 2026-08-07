#!/usr/bin/env bash

# Reference: https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/reference/ASLR_cmds.html#//apple_ref/doc/uid/TP40000983-CH216-SW59
osascript -e 'display notification "Your files have been backed up." with title "Backup complete" subtitle "Nightly backup" sound name "default"'

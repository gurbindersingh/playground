#!/bin/bash

logFile="$HOME/logs/battery-status.log"
status="$(pmset -g ps | grep -Eo '[0-9]{1,3}%; (dis)?charging')"
echo "[$(date +'%F %H:%M:%S')] Battery at $status." >> "$logFile" 2>&1

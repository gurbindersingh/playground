#!/usr/bin/env bash

logFile="$HOME/logs/battery-status.log"
status="$(pmset -g ps | grep -Eo '[0-9]{1,3}%; (dis)?charging')"
echo "[$(date +'%F %H:%M:%S')] Battery at $status." >> "$logFile" 2>&1

num="$(echo "$status" | grep -Eo '[0-9]{1,3}')"
if (( $num < 30 || $num > 70)); then
  shortcuts run "Battery Level" > /dev/null
fi

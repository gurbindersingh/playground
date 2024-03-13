#!/usr/bin/env bash
set -e

logFile="$HOME/logs/battery-status.log"
status="$(pmset -g ps | grep -Eo '[0-9]{1,3}%; (dis)?charg(ing|ed)')"
num="$(echo "$status" | grep -Eo '[0-9]{1,3}')"

echo "[$(date +'%F %H:%M:%S')] Battery at $status." >> "$logFile" 2>&1
if (( num < 30 || num > 75)); then
  shortcuts run "Battery Level" > /dev/null
fi

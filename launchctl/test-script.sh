#!/bin/bash

logFile="$HOME/logs/launchd-test.log"
now="$(date +'%F %H:%M:%S')"

echo "[$now] Ran" >> "$logFile" 2>&1

#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

now="$(date +'%T')"
theme="dark"
threshold="16:30:00"
# Source: https://www.timeanddate.com/sun/austria/vienna
# DST changes: last Sunday in March and October.
# The following are civil twilight times. They are gave as a range on website,
# so we use the larger of the two. Values rounded to the closest multiple of 5.
# sunrise=[0745 0720 0630 0630 0530 0455 0500 0535 0615 0655 0640 0725 0745]
#  sunset=[1650 1730 1815 2000 2050 2130 2140 2100 2000 1900 1705 1635 1650]
# Longest day: 16:05 h, summer solstice, around 21st June.
# Shortest day: 8:20 h, winter solstice, around 21st December.

if [[ "$now" < "$threshold" ]]; then
  theme="light"
fi
# echo "$theme"

currentWallpapers="$HOME/themed_wallpapers"
allWallpapers="$HOME/$(cat wallpaper-location.txt)"
currentTheme="$currentWallpapers/$theme"
logFile="$HOME/logs/set-wallpapers.log"

{
  echo ""
  if [[ -e "$currentTheme" ]]; then
    echo "[$(date +'%F %H:%M:%S')] Nothing to do."
    exit 0
  fi
  echo "[$(date +'%F %H:%M:%S')] Setting wallpapers for $theme theme."

  rm -r "${currentWallpapers:?}/"
  mkdir -p "$currentWallpapers"
  ln "$allWallpapers/$theme"/* "$currentWallpapers"
  touch "$currentWallpapers/$theme"

  echo "[$(date +'%F %H:%M:%S')] Done."
} >>"$logFile" 2>&1

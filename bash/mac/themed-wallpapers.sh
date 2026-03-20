#!/usr/bin/env bash
set -e

now="$(date +'%T')"
current_month=$(date +'%m')
theme="dark"
# Source: https://www.timeanddate.com/sun/austria/vienna
# Longest day: 16:05 h, summer solstice, around 21st June.
# Shortest day: 8:20 h, winter solstice, around 21st December.
# DST changes: last Sunday in March and October.
# The following are civil twilight times. They are gave as a range on website,
# so we use the larger of the two. Values rounded to the closest multiple of 5.
# (The 13th entry in the array is simply so I don't have to some modulo gymnastics.)
sunrise=(0745 0720 0630 0630 0530 0455 0500 0535 0615 0655 0640 0725 0745)
sunset=(1650 1730 1815 2000 2050 2130 2140 2100 2000 1900 1705 1635 1650)

echo "$now"
echo "$current_month"

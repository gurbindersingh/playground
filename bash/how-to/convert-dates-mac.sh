#!/usr/bin/env bash
now="$(date +'%F %H:%M:%S')"
date -jf '%Y-%m-%d %H:%M:%S' "$now" +"%s"

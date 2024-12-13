#!/usr/bin/env bash
set -e

. .config.sh

restic backup ./ 
unset RESTIC_PASSWORD

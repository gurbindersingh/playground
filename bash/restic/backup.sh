#!/usr/bin/env bash
set -e

. .config.sh

restic backup ./
bash .forget.sh
unset RESTIC_PASSWORD

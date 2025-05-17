#!/usr/bin/env bash
set -e

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

. ./example.config.sh

restic snapshots
unset $RESTIC_PASSWORD

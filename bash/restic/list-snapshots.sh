#!/usr/bin/env bash
set -e

. .config.sh

restic snapshots
unset $RESTIC_PASSWORD

#!/usr/bin/env bash
set -e

echo "[INFO] Listing current snapshots"
restic snapshots

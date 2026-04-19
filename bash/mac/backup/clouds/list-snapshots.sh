#!/usr/bin/env bash
set -e

restic --insecure-no-password snapshots

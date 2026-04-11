#!/usr/bin/env bash
set -e

if [[ "$#" -lt 1 ]]; then
  echo "Missing PATH parameter"
  echo "Usage: restic-backup PATH..."
  exit 1
fi

directory="$(dirname -- "${BASH_SOURCE[0]}")"
cd "$directory"

config="${XDG_CONFIG_HOME:-$HOME/.config}/cloud-backup.sh"
[ -r "$config" ] || {
  echo "Config not found: $config" >&2
  exit 1
}
. "$config"

backup_sources=("$@")

restic \
  --insecure-no-password backup \
  --skip-if-unchanged \
  --exclude-file "$HOME/.configs/restic-exclude-cloud" \
  "${backup_sources[@]:?}"
# --dry-run \
restic --insecure-no-password check

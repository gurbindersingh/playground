#!/usr/bin/env bash
set -e

usage() {
  echo "Usage: $(basename "$0") [OPTIONS] [FILE...]"
  echo ""
  echo "  Option:"
  echo "    -l  List files in bin"
  echo "    -p  Prune files older than 90 days"
  echo "    -e  Empty bin"
  echo "    -h  Show help"
  exit "$1"
}

error() {
  echo "$1" >&2
  usage "$2"
}

list_files() {
  echo "Files in trash bin:"
  eza -lA -s new "$trash_bin"
  echo ""
  echo "Total size: $(du -hs "$trash_bin/")"
  exit 0
}

empty_bin() {
  file_count="$(find "$trash_bin" -type f | wc -l)"

  if [[ $file_count -lt 1 ]]; then
    echo "The trash bin is empty"
    exit 0
  fi

  read -rp "Empty bin ($file_count files will be deleted)? (y/n) " confirm

  if [[ $confirm =~ [yY] ]]; then
    rm -rv "${trash_bin:?}"/*
  fi
  exit 0
}

prune() {
  file_count="$(find "$trash_bin" -type f -mtime +90 | wc -l)"

  if [[ $file_count -lt 1 ]]; then
    echo "No files older than 90 days."
    exit 0
  fi

  read -rp "Prune old files ($file_count files will be deleted)? (y/n) " confirm

  if [[ $confirm =~ [yY] ]]; then
    find "$trash_bin" -type f -mtime +90 -print -delete
  fi
  exit 0
}

# =============================================================================
# Main script
# =============================================================================

if [[ $# -lt 1 ]]; then
  usage 1
fi

trash_bin="$HOME/.trash-bin"
options=':hlep'

if [[ ! -e "$trash_bin" ]]; then
  echo "Creating $trash_bin"
  mkdir -vp "$trash_bin"
fi

while getopts "${options}" arg; do
  case ${arg} in
  e)
    empty_bin
    ;;
  h)
    usage 0
    ;;
  l)
    list_files
    ;;
  p)
    prune
    ;;
  :)
    error "Option -$OPTARG expects an argument." 2
    ;;
  ?)
    error "Invalid option: -${OPTARG}." 3
    ;;
  esac
done

echo ""
ls -1 "$@"
echo ""
read -rp "Move the files above to trash bin? (y/n): " confirm
echo ""

if [[ $confirm =~ [yY] ]]; then
  mv -v "$@" "$trash_bin"/
  exit 0
fi
exit 1

#!/bin/bash
set -e


usage() {
  echo "Usage: trash.sh [OPTIONS] [FILE...]"
  echo ""
  echo "  Option:"
  echo "    -e  Empty bin"
  echo "    -l  List files in bin"
  echo "    -h  Show help"
  exit "$1"
}


error() {
  echo "$1" >&2
  usage "$2"
}



list_files() {
  echo "Files in trash bin:"
  ls -lh "$trash_bin"
  exit 0
}


empty_bin() {
  file_count="$(find "$trash_bin" -type f | wc -l | tr -d ' ')"

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


# =============================================================================
# Main script
# =============================================================================

if [[ $# -lt 1 ]]; then
  usage 1
fi


trash_bin="$HOME/.trash-bin"
options=':hle'


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
    :)
      error "Option -$OPTARG expects an argument." 2
      ;;
    ?)
      error "Invalid option: -${OPTARG}." 3
      ;;
  esac
done


ls -1 "$@"
echo ""
read -rp "Delete the files above? (y/n): " confirm

if [[ $confirm =~ [yY] ]]; then
  mv -v "$@" "$trash_bin"/
fi

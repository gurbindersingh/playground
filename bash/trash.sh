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
  exit "$2"
}



list_files() {
  echo "Files in trash bin:"
  ls -lh "$trashcan"
  exit 0
}


empty_bin() {
  file_count="$(ls -1 | wc -l | tr -d ' ')"
  read -rp "Empty bin ($file_count files will be deleted)? (y/n) " confirm
  
  if [[ $confirm =~ [yY] ]]; then
    echo "Confirmed"
  fi
  exit 0
}


if [[ $# -lt 1 ]]; then
  usage 1
fi


trashcan="$HOME/.trash-can/"
optstring=':hle'


while getopts "${optstring}" arg; do
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

echo "Here"
# mv -v "$@" "$trashcan"

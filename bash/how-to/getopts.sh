#!/usr/bin/env bash
set -e

# Syntax: getopts optstring varname [arg ...]
# - optstring: a list of the valid option letters
#   - Starting the optstring with a colon (:), surpresses getopts generated error messages.
# - varname: the variable that receives the options one at a time
# - arg: is the optional list of parameters to be processed
#   - If arg is not present, getopts processes the command-line arguments.
# 
# - The getopts builtin uses the OPTIND (option index) and OPTARG (option argument) variables to track and store option-related values.
# - When a shell script starts, the value of OPTIND is 1.
# - Each time getopts is called and locates an argument, it increments OPTIND to the index of the next option to be processed.
# - If the option takes an argument, bash assigns the value of the argument to OPTARG
# 

optstring=':hab:'

while getopts "${optstring}" arg; do
  case ${arg} in
    h)
      echo "Usage message"
      ;;
    a)
      echo "Option a"
      ;;
    b)
      echo "Option b $OPTARG"
      ;;
    :)
      echo "$0: -$OPTARG expects an argument." >&2
      exit 1
      ;;
    ?)
      echo "Invalid option: -${OPTARG}."
      exit 2
      ;;
  esac
done
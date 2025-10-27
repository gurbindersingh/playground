#!/usr/bin/env bash

# Reminder: A non-zero code is considered an error.

(exit 0) || echo "1: This will not echo (or)"
(exit 1) || echo "2: This will echo (or)"

(exit 1) && echo "3: This will not echo (and)"
(exit 0) && echo "4: This will echo (and)"

(exit 0) && echo "5: This will echo (and+or)" || echo "6: This will not echo (and+or)"
(exit 0) || echo "7: This will not echo (or+and)" && echo "8: This will echo (or+and)"

# The condition in the parentheses will be executed in a subshell so the exit commands do not terminate this script.
(exit 0) || (echo "7: This will not echo (or+and+parentheses)" && echo "8: This will also not echo (or+and+parentheses)" && exit 1)
(exit 1) || (echo "9: This will echo (or+and+parentheses)" && echo "10: This will also echo (or+and+parentheses)" && exit 1)

# The commands in the braces will run in the current shell. So the last exit commands will terminate the script.
(exit 1) || {
  echo "11: This will echo (or+and+braces)"
  echo "12: This will also echo (or+and+braces)"
  echo "The script will exit with an error"
  exit 1
}

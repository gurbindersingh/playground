#!/usr/bin/env bash
set -e

# If the ssh-key is not, add it to the agent.
if ssh-add -l | grep -viq '<key name>'; then
  # -n makes it so that the echo doesn't print a new line.
  echo -n 'SSH key not found on agent. Add now? [y/n]: '
  read -r answer
  [ "$answer" != 'y' ] || ssh-add
fi

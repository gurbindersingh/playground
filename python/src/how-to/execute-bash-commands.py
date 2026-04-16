import subprocess
import sys
from typing import List

# https://stackoverflow.com/questions/4760215/running-shell-command-and-capturing-the-output


def runCommand(command: List[str]) -> str:
    # NOTE: List is deprecated as of 3.9
    #
    # IMPORTANT: Arguments do not require quotes
    result = subprocess.run(command, capture_output=True)
    errors = result.stderr.decode("utf-8")

    if errors and not errors.isspace():
        print(errors)
        sys.exit(1)

    return (result.stdout.decode("utf-8"))


# NOTE: os.system() is unsafe — it invokes a shell and is vulnerable to command
# injection if any part of the command comes from user input. Use subprocess.run()
# with a list of arguments (never shell=True) as shown below.
print(runCommand(["ls", "-lh"]))

import os
import subprocess
from typing import List

# https://stackoverflow.com/questions/4760215/running-shell-command-and-capturing-the-output


def runCommand(command: List[str]) -> str:
    # NOTE: List is deprecated as of 3.9
    # 
    # IMPORTANT: Arguments do not require quotes
    result = subprocess.run(command, capture_output=True)
    errors = result.stderr.decode("utf-8")

    if(len(errors) > 0 or not errors.isspace):
        print(errors)
        exit(1)

    return (result.stdout.decode("utf-8"))


# This is the simplest method. But will not capture output
os.system("ls -lh")
print("\n\n")
print(runCommand(["ls", "-lh"]))

import os
import subprocess

# Checks to see if the program was ran with the --gui flag
def should_use_cli(argv: list[str]) -> bool:
    return "--gui" not in argv

# Simple utility that clears the terminal and uses the correct command based on OS type
# nt = windows
# else = macos & linux!
def clear_terminal():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

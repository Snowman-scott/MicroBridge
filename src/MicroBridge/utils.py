# Checks to see if the program was ran with the --gui flag or without any arguments
def should_use_cli(argv: list[str]) -> bool:
    if not argv:
        return False
    lowered = [arg.lower() for arg in argv]
    return "--gui" not in lowered

# Simple utility that clears the terminal and uses the correct command based on OS type
# nt = windows
# else = macos & linux!
# Not used atm
# def clear_terminal():
#     import os
#     import subprocess
#     subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

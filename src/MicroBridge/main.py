import sys
from MicroBridge.utils import clear_terminal
from MicroBridge.utils import should_use_cli


def main():
    clear_terminal()
    argv = sys.argv[1:]
    if should_use_cli(argv):
        from MicroBridge.CLI.cli import run as cli_run
        cli_run.main(args=argv)
    else:
        pass # Will be GUI

if __name__ == "__main__":
    main()

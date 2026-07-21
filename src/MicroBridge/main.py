import sys
from MicroBridge.utils import should_use_cli


def main():
    argv = sys.argv[1:]
    if should_use_cli(argv):
        from MicroBridge.CLI.cli import run as cli_run
        cli_run.main(args=argv)
    else:
        print("Hello, This will be a GUI soon :3")

if __name__ == "__main__":
    main()

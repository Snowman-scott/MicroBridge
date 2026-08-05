import sys
from MicroBridge.utils import should_use_cli


def hide_console():
    import os
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, 0)


def main():
    argv = sys.argv[1:]
    if should_use_cli(argv):
        from MicroBridge.CLI.cli import run as cli_run
        cli_run.main(args=argv)
    else:
        hide_console()
        from MicroBridge.GUI.gui import run as gui_run
        gui_run()

if __name__ == "__main__":
    main()

import os
import sys

from MicroBridge.utils import should_use_cli


def hide_console():
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, 0)


def attach_parent_console():
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        return
    import ctypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    if kernel32.AttachConsole(-1):
        sys.stdout = open('CONOUT$', 'w')
        sys.stderr = open('CONOUT$', 'w')
        sys.stdin = open('CONIN$', 'r')
    else:
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')


def main():
    argv = sys.argv[1:]
    if should_use_cli(argv):
        attach_parent_console()
        from MicroBridge.CLI.cli import run as cli_run
        cli_run.main(args=argv)
    else:
        hide_console()
        from MicroBridge.GUI.gui import run as gui_run
        gui_run()

if __name__ == "__main__":
    main()

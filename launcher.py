"""Cross-platform desktop entry point. Run with Python 3.10 or later."""

import sys


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required / Python 3.10 minimum.")
    try:
        import tkinter
    except ImportError as exc:
        raise SystemExit(
            "Install Python with Tcl/Tk to use the launcher. You can also run: python serveur.py --host 127.0.0.1 --lang en"
        ) from exc
    from eco.desktop import main as desktop_main

    try:
        desktop_main()
    except tkinter.TclError as exc:
        raise SystemExit(
            "Desktop unavailable: %s. Use: python serveur.py --host 127.0.0.1 --lang en" % exc
        ) from exc


if __name__ == "__main__":
    main()

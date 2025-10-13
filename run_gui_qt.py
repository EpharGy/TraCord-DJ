"""Entry point for the TraCord DJ PySide6 GUI."""
from __future__ import annotations

import argparse
import logging
import sys

from ui_qt2.app import create_application
from ui_qt2.controller import QtController
from ui_qt2.log_bridge import install_qt_log_handler
from ui_qt2.main_window import MainWindow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the TraCord DJ Qt GUI")
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_level = getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    install_qt_log_handler(log_level)

    app = create_application()
    window = MainWindow()
    QtController(window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

"""Application bootstrap utilities for the PySide6 GUI (v2)."""
from __future__ import annotations

import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets


def _enable_high_dpi() -> None:
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)  # type: ignore[attr-defined]
    except Exception:
        pass


def create_application(argv: list[str] | None = None) -> QtWidgets.QApplication:
    if QtWidgets.QApplication.instance():
        return QtWidgets.QApplication.instance()  # type: ignore[return-value]

    _enable_high_dpi()
    app = QtWidgets.QApplication(argv or sys.argv)
    try:
        app.setStyle("Fusion")
    except Exception:
        pass
    app.setOrganizationName("TraCord DJ")
    app.setApplicationName("TraCord DJ")

    palette = QtGui.QPalette()
    cr = QtGui.QPalette.ColorRole
    palette.setColor(cr.Window, QtGui.QColor("#1e1e1e"))
    palette.setColor(cr.WindowText, QtGui.QColor("#f0f0f0"))
    palette.setColor(cr.Base, QtGui.QColor("#2c2c2c"))
    palette.setColor(cr.AlternateBase, QtGui.QColor("#333333"))
    palette.setColor(cr.Text, QtGui.QColor("#f0f0f0"))
    palette.setColor(cr.Button, QtGui.QColor("#3c3c3c"))
    palette.setColor(cr.ButtonText, QtGui.QColor("#f0f0f0"))
    palette.setColor(cr.Highlight, QtGui.QColor("#3a86ff"))
    palette.setColor(cr.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget { color: #e6e6e6; }
        QGroupBox { border: 1px solid #444; border-radius: 6px; margin-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #f0f0f0; font-weight: 600; }

        QPushButton { background-color: #2f2f2f; color: #f5f5f5; border: 1px solid #555; border-radius: 4px; padding: 4px 10px; }
        QPushButton:hover { background-color: #3a3a3a; }
        QPushButton:pressed { background-color: #262626; }
        QPushButton:disabled { background-color: #1e1e1e; color: #777; border: 1px solid #3a3a3a; }

        QHeaderView::section { background-color: #2b2b2b; color: #e6e6e6; padding: 6px 8px; border: 1px solid #454545; }
        QTableCornerButton::section { background-color: #2b2b2b; border: 1px solid #454545; }

        QPlainTextEdit, QTextEdit { background-color: #202020; color: #eaeaea; border: 1px solid #3a3a3a; }
        QLineEdit { background-color: #2a2a2a; color: #f0f0f0; border: 1px solid #3a3a3a; border-radius: 3px; padding: 3px 6px; }
        QComboBox, QSpinBox, QDoubleSpinBox { background-color: #2a2a2a; color: #f0f0f0; border: 1px solid #3a3a3a; border-radius: 3px; padding: 2px 6px; }

        QScrollBar:vertical { background: #1e1e1e; width: 12px; margin: 0; }
        QScrollBar::handle:vertical { background: #3a3a3a; min-height: 20px; border-radius: 5px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

        QScrollBar:horizontal { background: #1e1e1e; height: 12px; margin: 0; }
        QScrollBar::handle:horizontal { background: #3a3a3a; min-width: 20px; border-radius: 5px; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """
    )

    font = QtGui.QFont("Segoe UI", 9)
    app.setFont(font)

    icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))

    return app

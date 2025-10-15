"""Log panel (v2) with styled HTML output."""
from __future__ import annotations

from PySide6 import QtGui, QtWidgets


class LogPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Log", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setReadOnly(True)
        # Use the application default font for a cleaner, native look
        try:
            self.text_edit.setFont(QtWidgets.QApplication.font())
        except Exception:
            pass
        layout.addWidget(self.text_edit)

    def _styles_for_level(self, level: str) -> tuple[str, str]:
        lvl = (level or "info").lower()
        # badge_bg, badge_fg
        if lvl == "error":
            return ("#2a0000", "#ff4d4f")
        if lvl == "warning":
            return ("#2a1f00", "#f0ad4e")
        if lvl == "success":
            return ("#072a14", "#8fda8f")
        if lvl == "debug":
            return ("#081a2a", "#78a6f5")
        return ("#111318", "#d0d4db")  # info/default

    def append_log(self, message: str, level: str) -> None:
        bg, fg = self._styles_for_level(level)
        lvl_text = (level or "info").upper()
        # Safe-escape message for HTML
        safe = QtWidgets.QLabel().textFormat()  # noop to keep Qt types alive
        from html import escape as _html_escape
        msg_html = _html_escape(message)
        badge = (
            f"<span style='display:inline-block;padding:1px 6px;margin-right:8px;"
            f"border-radius:4px;background:{bg};color:{fg};font-weight:600;'>[{lvl_text}]</span>"
        )
        line = f"<div style='color:#d0d4db; line-height:1.35'>{badge}{msg_html}</div>"
        self.text_edit.append(line)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

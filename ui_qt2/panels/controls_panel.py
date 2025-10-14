"""Control buttons panel (v2)."""
from __future__ import annotations

from typing import Callable, Dict

from PySide6 import QtCore, QtWidgets


class ControlsPanel(QtWidgets.QGroupBox):
    _ACTIONS = [
        ("bot", "▶ Start Bot"),
        ("refresh", "🔄 Refresh Collection"),
        ("reset_session", "♻ Reset Session Stats"),
        ("reset_global", "🗑 Reset Global Stats"),
        ("settings", "⚙ Settings"),
    ]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Controls", parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)

        self._buttons: Dict[str, QtWidgets.QPushButton] = {}
        for key, title in self._ACTIONS:
            button = QtWidgets.QPushButton(title)
            button.setObjectName(f"controls_{key}")
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button)
            self._buttons[key] = button

        layout.addStretch(1)

    def bind(self, action: str, callback: Callable[[], None]) -> None:
        button = self._buttons.get(action)
        if not button:
            raise KeyError(f"Unknown controls action: {action}")
        button.clicked.connect(callback)  # type: ignore[arg-type]

    def set_enabled(self, action: str, enabled: bool) -> None:
        button = self._buttons.get(action)
        if button:
            button.setEnabled(enabled)

    def set_all_enabled(self, enabled: bool) -> None:
        for button in self._buttons.values():
            button.setEnabled(enabled)

    # --- Convenience helpers for dynamic labels ---
    def set_button_text(self, action: str, text: str) -> None:
        button = self._buttons.get(action)
        if button:
            button.setText(text)

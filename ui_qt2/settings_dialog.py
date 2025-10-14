"""Settings dialog for editing settings.json (Qt v2) with grouped fields and help text."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from PySide6 import QtCore, QtWidgets

from config.settings import SETTINGS_PATH


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(640, 700)

        self._widgets: dict[str, QtWidgets.QWidget] = {}
        self._data: Dict[str, Any] = {}

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Scroll area with a form layout inside
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        inner = QtWidgets.QWidget(scroll)
        scroll.setWidget(inner)
        main_layout.addWidget(scroll, 1)

        # Buttons
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box, 0)

        # Load data and build form
        self._load()
        self._build_grouped_form(inner)

    def _load(self) -> None:
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    # --- Form building helpers ---
    def _build_grouped_form(self, container: QtWidgets.QWidget) -> None:
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        groups: Dict[str, List[str]] = {
            "Discord": [
                "DISCORD_TOKEN",
                "DISCORD_BOT_APP_ID",
                "DISCORD_BOT_CHANNEL_IDS",
                "DISCORD_BOT_ADMIN_IDS",
                "DISCORD_LIVE_NOTIFICATION_ROLES",
            ],
            "Traktor": [
                "TRAKTOR_LOCATION",
                "TRAKTOR_COLLECTION_FILENAME",
                "TRAKTOR_BROADCAST_PORT",
            ],
            "GUI & Overlay": [
                "CONSOLE_PANEL_WIDTH",
                "COVER_SIZE",
                "FADE_STYLE",
                "FADE_FRAMES",
                "FADE_DURATION",
                "SPOUT_BORDER_PX",
                "SPOUT_COVER_SIZE",
                "DEBUG",
            ],
            "MIDI": [
                "MIDI_DEVICE",
            ],
            "Search & Lists": [
                "NEW_SONGS_DAYS",
                "MAX_SONGS",
                "TIMEOUT",
            ],
            "Exclusions": [
                "EXCLUDED_ITEMS",
            ],
        }

        descriptions: Dict[str, str] = {
            "DISCORD_TOKEN": "Discord bot token (keep secret).",
            "DISCORD_BOT_APP_ID": "Discord Application (Client) ID.",
            "DISCORD_BOT_CHANNEL_IDS": "Allowed channel IDs for commands, comma-separated.",
            "DISCORD_BOT_ADMIN_IDS": "Admin user IDs, comma-separated.",
            "DISCORD_LIVE_NOTIFICATION_ROLES": "Role names/IDs to mention for live notifications, comma-separated.",
            "TRAKTOR_LOCATION": "Path to the parent folder that contains 'Traktor X.X.X' subfolders.",
            "TRAKTOR_COLLECTION_FILENAME": "Collection filename (usually collection.nml).",
            "TRAKTOR_BROADCAST_PORT": "Port used by Traktor broadcast (match Traktor settings).",
            "CONSOLE_PANEL_WIDTH": "UI content width (pixels).",
            "COVER_SIZE": "Cover art size for UI/overlay base64 variant (px).",
            "FADE_STYLE": "Cover art transition style: 'fade' (fade to transparent then in) or 'crossfade' (blend old→new).",
            "FADE_FRAMES": "Number of frames in the transition (higher = smoother).",
            "FADE_DURATION": "Total transition duration in seconds.",
            "SPOUT_BORDER_PX": "Transparent border padding around cover art (px).",
            "SPOUT_COVER_SIZE": "Spout output size (square px).",
            "DEBUG": "Enable extra logging.",
            "MIDI_DEVICE": "Preferred MIDI output device name (exact or partial match).",
            "NEW_SONGS_DAYS": "Days back for 'new songs' listing.",
            "MAX_SONGS": "Maximum items for certain listings.",
            "TIMEOUT": "Timeout (seconds) for interactive selections.",
            "EXCLUDED_ITEMS": "JSON object with DIR/FILE substrings to ignore (advanced).",
        }

        seen: Set[str] = set()

        def add_group(title: str, keys: List[str]) -> None:
            box = QtWidgets.QGroupBox(title)
            form = QtWidgets.QFormLayout(box)
            form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            for key in keys:
                if key not in self._data:
                    continue
                seen.add(key)
                value = self._data.get(key)
                label = QtWidgets.QLabel(key)
                label.setMinimumWidth(220)
                tip = descriptions.get(key)
                if tip:
                    label.setToolTip(tip)

                widget = self._create_editor_for(key, value)
                if tip:
                    widget.setToolTip(tip)  # type: ignore[attr-defined]
                self._widgets[key] = widget
                form.addRow(label, widget)
            if form.rowCount() > 0:
                layout.addWidget(box)

        # Add configured groups in order
        for group_title, keys in groups.items():
            add_group(group_title, keys)

        # Any remaining keys → Other
        remaining = [k for k in sorted(self._data.keys()) if k not in seen]
        if remaining:
            add_group("Other", remaining)

        layout.addStretch(1)

    def _create_editor_for(self, key: str, value: Any) -> QtWidgets.QWidget:
        # Specialized editors
        if key == "FADE_STYLE":
            combo = QtWidgets.QComboBox()
            combo.addItems(["fade", "crossfade"])
            try:
                idx = ["fade", "crossfade"].index(str(value).lower())
            except Exception:
                idx = 0
            combo.setCurrentIndex(idx)
            return combo

        # Generic mapping by type
        if isinstance(value, bool):
            w = QtWidgets.QCheckBox()
            w.setChecked(bool(value))
            return w
        if isinstance(value, int):
            w = QtWidgets.QSpinBox()
            w.setRange(-1_000_000_000, 1_000_000_000)
            w.setValue(int(value))
            return w
        if isinstance(value, float):
            w = QtWidgets.QDoubleSpinBox()
            w.setDecimals(3)
            w.setRange(-1_000_000.0, 1_000_000.0)
            w.setSingleStep(0.1)
            w.setValue(float(value))
            return w
        if isinstance(value, list):
            return QtWidgets.QLineEdit(
                ", ".join(str(x) for x in value)
            )
        if isinstance(value, dict):
            w = QtWidgets.QPlainTextEdit()
            w.setPlainText(json.dumps(value, indent=2, ensure_ascii=False))
            w.setMinimumHeight(90)
            return w
        # string or other
        w = QtWidgets.QLineEdit(str(value))
        if "TOKEN" in key.upper():
            w.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        return w

    def _on_save(self) -> None:
        # Build updated data
        updated: Dict[str, Any] = dict(self._data)
        for key, widget in self._widgets.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                updated[key] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QSpinBox):
                updated[key] = int(widget.value())
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                updated[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QPlainTextEdit):
                # Parse JSON text
                text = widget.toPlainText().strip()
                try:
                    updated[key] = json.loads(text) if text else {}
                except Exception:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Invalid JSON",
                        f"The value for '{key}' is not valid JSON. Please correct it.",
                    )
                    return
            elif isinstance(widget, QtWidgets.QComboBox):
                updated[key] = widget.currentText().strip()
            elif isinstance(widget, QtWidgets.QLineEdit):
                text = widget.text().strip()
                if key == "FADE_STYLE":
                    updated[key] = text if text in ("fade", "crossfade") else "fade"
                elif isinstance(self._data.get(key), list):
                    # Parse comma-separated lists; coerce to int where possible
                    items = [t.strip() for t in text.split(",") if t.strip()]
                    parsed: list[Any] = []
                    for it in items:
                        if it.isdigit():
                            try:
                                parsed.append(int(it))
                                continue
                            except Exception:
                                pass
                        parsed.append(it)
                    updated[key] = parsed
                else:
                    updated[key] = text

        # Persist back to settings.json
        try:
            try:
                from utils.helpers import safe_write_json

                safe_write_json(SETTINGS_PATH, updated, indent=2, ensure_ascii=False)
            except Exception:
                with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                    json.dump(updated, f, indent=2, ensure_ascii=False)

            QtWidgets.QMessageBox.information(
                self,
                "Settings saved",
                "Settings saved. Please restart the application for changes to take effect.",
            )
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Save failed",
                f"Could not save settings.json:\n{e}",
            )

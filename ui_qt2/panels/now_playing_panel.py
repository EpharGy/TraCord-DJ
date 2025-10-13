"""Now playing panel (v2) with cover art and controls."""
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class NowPlayingPanel(QtWidgets.QGroupBox):
    toggledListener = QtCore.Signal(bool)
    toggledSpout = QtCore.Signal(bool)
    toggledMidi = QtCore.Signal(bool)
    overlayRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Now Playing", parent)
        layout = QtWidgets.QGridLayout(self)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)

        # Buttons row
        button_bar = QtWidgets.QHBoxLayout()
        button_bar.setSpacing(6)
        self.listener_button = QtWidgets.QPushButton("Enable Listener")
        self.listener_button.setCheckable(True)
        self.spout_button = QtWidgets.QPushButton("Enable Spout")
        self.spout_button.setCheckable(True)
        self.overlay_button = QtWidgets.QPushButton("Open Overlay")
        self.midi_button = QtWidgets.QPushButton("Enable MIDI")
        self.midi_button.setCheckable(True)
        for b in (self.listener_button, self.spout_button, self.overlay_button, self.midi_button):
            button_bar.addWidget(b)
        button_bar.addStretch(1)
        layout.addLayout(button_bar, 0, 0, 1, 2)

        # Cover art preview
        self.cover_label = QtWidgets.QLabel()
        self.cover_label.setFixedSize(220, 220)
        self.cover_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #202020; border: 1px solid #404040;")
        layout.addWidget(self.cover_label, 1, 0)

        # Track info
        self.info_label = QtWidgets.QLabel("No track playing.")
        self.info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label, 1, 1)

        # Wire signals
        self.listener_button.toggled.connect(self.toggledListener.emit)
        self.spout_button.toggled.connect(self.toggledSpout.emit)
        self.midi_button.toggled.connect(self.toggledMidi.emit)
        self.overlay_button.clicked.connect(self.overlayRequested.emit)

    def set_track_info(self, text: str) -> None:
        self.info_label.setText(text)

    def set_cover_pixmap(self, pixmap: Optional[QtGui.QPixmap]) -> None:
        if pixmap:
            scaled = pixmap.scaled(
                self.cover_label.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.cover_label.setPixmap(scaled)
        else:
            self.cover_label.clear()

    def set_listener_state(self, enabled: bool) -> None:
        self.listener_button.blockSignals(True)
        self.listener_button.setChecked(enabled)
        self.listener_button.blockSignals(False)
        self.listener_button.setText("Disable Listener" if enabled else "Enable Listener")

    def set_spout_state(self, enabled: bool) -> None:
        self.spout_button.blockSignals(True)
        self.spout_button.setChecked(enabled)
        self.spout_button.blockSignals(False)
        self.spout_button.setText("Disable Spout" if enabled else "Enable Spout")

    def set_midi_state(self, enabled: bool) -> None:
        self.midi_button.blockSignals(True)
        self.midi_button.setChecked(enabled)
        self.midi_button.blockSignals(False)
        self.midi_button.setText("Disable MIDI" if enabled else "Enable MIDI")

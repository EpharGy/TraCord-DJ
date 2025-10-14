"""Now playing panel (v2) with cover art and controls."""
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class ElideLabel(QtWidgets.QLabel):
    """Single-line QLabel that elides overflowing text with an ellipsis."""

    def __init__(
        self,
        text: str = "",
        parent: QtWidgets.QWidget | None = None,
        elide_mode: QtCore.Qt.TextElideMode = QtCore.Qt.TextElideMode.ElideRight,
    ) -> None:
        super().__init__(parent)
        self._full_text = text or ""
        self._elide_mode = elide_mode
        self.setWordWrap(False)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.setText(self._full_text)

    def setText(self, text: str) -> None:  # type: ignore[override]
        self._full_text = text or ""
        self._apply_elide()

    def fullText(self) -> str:
        return self._full_text

    def setElideMode(self, mode: QtCore.Qt.TextElideMode) -> None:
        self._elide_mode = mode
        self._apply_elide()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        metrics = self.fontMetrics()
        width = max(0, self.width())
        elided = metrics.elidedText(self._full_text, self._elide_mode, width)
        super().setText(elided)


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
        from config.settings import Settings
        self.cover_label = QtWidgets.QLabel()
        # Display at min(COVER_SIZE, 150): you can go smaller by lowering COVER_SIZE,
        # but cannot exceed 150 without increasing the generated image size.
        cover_sz = int(getattr(Settings, 'COVER_SIZE', 200) or 200)
        gui_cover_sz = int(min(cover_sz, 150))
        self.cover_label.setFixedSize(gui_cover_sz, gui_cover_sz)
        self.cover_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #202020; border: 1px solid #404040;")
        layout.addWidget(self.cover_label, 1, 0)

        # Track info (separate labels so fonts can be adjusted independently)
        info_col = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(info_col)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self.artist_label = ElideLabel("")
        self.title_label = ElideLabel("")
        self.album_label = ElideLabel("")
        self.extra_label = QtWidgets.QLabel("")
        for lbl in (self.artist_label, self.title_label, self.album_label, self.extra_label):
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        # Only the extra label should wrap
        self.extra_label.setWordWrap(True)

        # Default fonts (you can tweak these)
        # Artist: large bold
        f_artist = self.artist_label.font(); f_artist.setPointSize(20); f_artist.setBold(True); self.artist_label.setFont(f_artist)
        # Title: medium semibold
        f_title = self.title_label.font(); f_title.setPointSize(18); f_title.setWeight(QtGui.QFont.Weight.Medium); self.title_label.setFont(f_title)
        # Album: small italic
        f_album = self.album_label.font(); f_album.setPointSize(16); f_album.setItalic(True); self.album_label.setFont(f_album)
        # Extra: small normal
        f_extra = self.extra_label.font(); f_extra.setPointSize(14); self.extra_label.setFont(f_extra)

        info_layout.addWidget(self.artist_label)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.album_label)
        info_layout.addWidget(self.extra_label)
        info_layout.addStretch(1)
        layout.addWidget(info_col, 1, 1)

        # Wire signals
        self.listener_button.toggled.connect(self.toggledListener.emit)
        self.spout_button.toggled.connect(self.toggledSpout.emit)
        self.midi_button.toggled.connect(self.toggledMidi.emit)
        self.overlay_button.clicked.connect(self.overlayRequested.emit)

    def set_track_info(self, text: str) -> None:
        """Compatibility shim: expects 'Artist\nTitle\n[Album]\nExtra' style text."""
        lines = (text or "").splitlines()
        artist = lines[0] if len(lines) > 0 else ""
        title = lines[1] if len(lines) > 1 else ""
        album = lines[2] if len(lines) > 2 else ""
        extra = lines[3] if len(lines) > 3 else ""
        self.set_track_fields(artist, title, album, extra)

    def set_track_fields(self, artist: str, title: str, album: str, extra: str) -> None:
        self.artist_label.setText(artist or "")
        self.title_label.setText(title or "")
        self.album_label.setText(f"[{album}]" if album else "")
        self.extra_label.setText(extra or "")

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

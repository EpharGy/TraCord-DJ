"""Harmonic Mixing popup dialog."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence

from PySide6 import QtCore, QtWidgets

from utils.harmonic_keys import (
    open_key_int_to_str,
    open_key_int_to_straight_key,
    shift_key_by_semitones,
)


def _format_search_row(song: Dict[str, Any]) -> str:
    artist = str(song.get("artist", "")).strip()
    title = str(song.get("title", "")).strip()
    album = str(song.get("album", "")).strip()
    bpm = song.get("bpm")
    bpm_txt = f"{bpm:.1f}" if isinstance(bpm, (int, float)) else str(bpm or "")
    mk_raw = song.get("musical_key")
    mk = None
    if mk_raw not in (None, "", []):
        try:
            mk = int(mk_raw)
        except Exception:
            mk = mk_raw if isinstance(mk_raw, int) else None
    key_txt = open_key_int_to_str(mk) if isinstance(mk, int) else ""
    album_txt = f" [{album}]" if album else ""
    return f"[{bpm_txt}] | [{key_txt}] | {artist} - {title}{album_txt}"


def _format_selection(song: Dict[str, Any], anchor_bpm: float | None, *, show_deviation: bool) -> str:
    if not song:
        return "Not set"
    artist = str(song.get("artist", "")).strip()
    title = str(song.get("title", "")).strip()
    album = str(song.get("album", "")).strip()
    bpm = song.get("bpm")
    mk_raw = song.get("musical_key")
    mk = None
    if mk_raw not in (None, "", []):
        try:
            mk = int(mk_raw)
        except Exception:
            mk = mk_raw if isinstance(mk_raw, int) else None
    try:
        orig_bpm = float(bpm) if bpm not in (None, "") else None
    except Exception:
        orig_bpm = None

    orig_key = open_key_int_to_str(mk) if isinstance(mk, int) else ""
    lines: List[str] = []
    title_line = f"{artist} - {title}".strip(" -")
    lines.append(title_line or "(unknown)")
    if album:
        lines.append(album)

    if orig_bpm is None:
        bpm_part = ""
    else:
        bpm_part = f"{orig_bpm:.1f}"

    adjusted_key = ""
    deviation_txt = ""
    if anchor_bpm and orig_bpm and orig_bpm > 0:
        ratio = anchor_bpm / orig_bpm
        semitone_shift = 12.0 * math.log2(max(ratio, 1e-9))
        adj_key_int = shift_key_by_semitones(mk, semitone_shift) if mk is not None else None
        adjusted_key = open_key_int_to_str(adj_key_int) if adj_key_int is not None else ""
        deviation_pct = (ratio - 1.0) * 100.0
        deviation_txt = f"{deviation_pct:+.1f}%"

    bpm_line_parts: List[str] = []
    if bpm_part:
        if show_deviation:
            # Song B: show its own BPM (no anchor override)
            bpm_line_parts.append(bpm_part)
        else:
            # Song A: show shift toward current BPM
            bpm_line_parts.append(f"{bpm_part} -> {anchor_bpm:.1f}" if anchor_bpm else bpm_part)
            if deviation_txt:
                bpm_line_parts.append(f"({deviation_txt})")
    if show_deviation:
        # Song B: show target key only
        if orig_key:
            bpm_line_parts.append(orig_key)
    else:
        # Song A: show key shift if anchor differs
        key_text = orig_key if orig_key else ""
        if adjusted_key:
            key_text = f"{orig_key} -> {adjusted_key}" if orig_key else adjusted_key
        if key_text:
            bpm_line_parts.append(key_text)

    bpm_line = " | ".join(part for part in bpm_line_parts if part)
    if bpm_line:
        lines.append(bpm_line)
    return "\n".join(lines)


class HarmonicMixPopup(QtWidgets.QDialog):
    def __init__(self, controller, library: Sequence[Dict[str, Any]]):
        # No parent to avoid raising main window when focusing this popup
        super().__init__(None)
        self.controller = controller
        self.library: List[Dict[str, Any]] = list(library or [])
        self.song_a: Dict[str, Any] | None = None
        self.song_b: Dict[str, Any] | None = None
        self.setWindowTitle("Harmonic Mixing")
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(880, 640)

        layout = QtWidgets.QVBoxLayout(self)

        # Controls row
        ctl_row = QtWidgets.QHBoxLayout()
        self.current_bpm_lbl = QtWidgets.QLabel("Current BPM: —")
        self.mode_checkbox = QtWidgets.QCheckBox("Key-only (ignore BPM)")
        self.tolerance_spin = QtWidgets.QDoubleSpinBox()
        self.tolerance_spin.setRange(0, 25)
        self.tolerance_spin.setSingleStep(0.5)
        self.tolerance_spin.setValue(5.0)
        ctl_row.addWidget(self.current_bpm_lbl)
        ctl_row.addStretch(1)
        ctl_row.addWidget(QtWidgets.QLabel("BPM tolerance %:"))
        ctl_row.addWidget(self.tolerance_spin)
        ctl_row.addWidget(self.mode_checkbox)
        layout.addLayout(ctl_row)

        # Song selectors
        selectors = QtWidgets.QHBoxLayout()
        self.a_group = self._build_song_box("Song A", allow_current=True)
        self.b_group = self._build_song_box("Song B", allow_current=False)
        selectors.addWidget(self.a_group)
        selectors.addWidget(self.b_group)
        layout.addLayout(selectors)

        # Search panel
        search_box = QtWidgets.QGroupBox("Search Library")
        sb_layout = QtWidgets.QGridLayout(search_box)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_results = QtWidgets.QListWidget()
        self.search_results.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.search_results.setMinimumHeight(180)
        set_a_btn = QtWidgets.QPushButton("Set as Song A")
        set_b_btn = QtWidgets.QPushButton("Set as Song B")
        refresh_btn = QtWidgets.QPushButton("Search")

        sb_layout.addWidget(QtWidgets.QLabel("Search (artist/title/album)"), 0, 0)
        sb_layout.addWidget(self.search_edit, 0, 1, 1, 2)
        sb_layout.addWidget(refresh_btn, 0, 3, 1, 1)
        sb_layout.addWidget(self.search_results, 1, 0, 1, 4)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(set_a_btn)
        btn_row.addWidget(set_b_btn)
        sb_layout.addLayout(btn_row, 2, 0, 1, 4)

        layout.addWidget(search_box)

        # Actions
        actions = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton("Find Transitions")
        self.clear_btn = QtWidgets.QPushButton("Clear Results")
        self.save_btn = QtWidgets.QPushButton("Save Playlist")
        self.clear_playlist_btn = QtWidgets.QPushButton("Clear Playlist")
        self.remove_first_btn = QtWidgets.QPushButton("Remove First Hop")
        self.reapply_bpm_btn = QtWidgets.QPushButton("Reapply Current BPM")
        actions.addWidget(self.run_btn)
        actions.addWidget(self.clear_btn)
        actions.addWidget(self.remove_first_btn)
        actions.addWidget(self.reapply_bpm_btn)
        actions.addStretch(1)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.clear_playlist_btn)
        layout.addLayout(actions)

        # Results tree
        self.columns_area = QtWidgets.QScrollArea()
        self.columns_area.setWidgetResizable(True)
        self.columns_container = QtWidgets.QWidget()
        self.columns_layout = QtWidgets.QHBoxLayout(self.columns_container)
        self.columns_layout.setContentsMargins(4, 4, 4, 4)
        self.columns_layout.setSpacing(8)
        self.columns_area.setWidget(self.columns_container)
        layout.addWidget(self.columns_area, stretch=1)

        # Status label (hidden unless showing an error)
        self.status_lbl = QtWidgets.QLabel("")
        self.status_lbl.setVisible(False)
        layout.addWidget(self.status_lbl)

        # State for column selections
        self.current_path: Dict[str, Any] | None = None
        self.selected_by_hop: Dict[int, Dict[str, Any]] = {}
        self.column_widgets: Dict[int, QtWidgets.QListWidget] = {}

        # Wire events
        refresh_btn.clicked.connect(self._refresh_search)
        set_a_btn.clicked.connect(lambda: self._set_from_selection("A"))
        set_b_btn.clicked.connect(lambda: self._set_from_selection("B"))
        self.run_btn.clicked.connect(self._run_matching)
        self.clear_btn.clicked.connect(self._clear_results)
        self.save_btn.clicked.connect(self._save_playlist)
        self.clear_playlist_btn.clicked.connect(self._clear_playlist)
        self.remove_first_btn.clicked.connect(self._remove_first_hop)
        self.reapply_bpm_btn.clicked.connect(self._reapply_current_bpm)

        self._refresh_current_track_state()
        self._refresh_search()

        # Poll current BPM to keep display in sync with overlay/MIDI
        self._bpm_timer = QtCore.QTimer(self)
        self._bpm_timer.setInterval(1000)
        self._bpm_timer.timeout.connect(self._refresh_current_track_state)
        self._bpm_timer.start()

    # --- UI builders
    def _build_song_box(self, title: str, *, allow_current: bool) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(title)
        v = QtWidgets.QVBoxLayout(box)
        lbl = QtWidgets.QLabel("Not set")
        lbl.setWordWrap(True)
        btn_row = QtWidgets.QHBoxLayout()
        if allow_current:
            use_cur = QtWidgets.QPushButton("Use Current Track")
            use_cur.clicked.connect(lambda: self.controller.set_harmonic_song_from_current())
            btn_row.addWidget(use_cur)
            self.use_current_btn = use_cur
            apply_bpm_btn = QtWidgets.QPushButton("Apply Current BPM")
            apply_bpm_btn.clicked.connect(self._apply_current_bpm_to_song_a)
            btn_row.addWidget(apply_bpm_btn)
        clear_btn = QtWidgets.QPushButton("Clear")
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)
        v.addWidget(lbl)
        v.addLayout(btn_row)
        if allow_current:
            self.a_label = lbl
            self.a_clear_btn = clear_btn
        else:
            self.b_label = lbl
            self.b_clear_btn = clear_btn
        clear_btn.clicked.connect(lambda: self._clear_selection("A" if allow_current else "B"))
        return box

    def _apply_current_bpm_to_song_a(self) -> None:
        # Just re-render Song A using current BPM anchor
        if self.song_a:
            self.set_song_selection("A", self.song_a)
        # Also refresh label and matches to reflect current BPM
        self._refresh_current_track_state()
        self._run_matching()

    # --- Public setters from controller
    def set_song_selection(self, role: str, song: Dict[str, Any] | None) -> None:
        target = (self.a_label if role == "A" else self.b_label)
        if role == "A":
            self.song_a = song
        else:
            self.song_b = song
        anchor = self.controller.get_anchor_bpm()
        display = _format_selection(song or {}, anchor, show_deviation=(role == "B")) if song else "Not set"
        target.setText(display or "Not set")

    def refresh_now_playing_state(self) -> None:
        self._refresh_current_track_state()

    # --- Internal helpers
    def _refresh_current_track_state(self) -> None:
        bpm = self.controller.get_anchor_bpm()
        if bpm:
            self.current_bpm_lbl.setText(f"Current BPM: {bpm:.1f}")
        else:
            self.current_bpm_lbl.setText("Current BPM: —")
        can_use = self.controller.current_track_has_key_bpm()
        if hasattr(self, "use_current_btn"):
            self.use_current_btn.setEnabled(can_use)
        # Refresh displayed selections to reflect current BPM adjustments
        if self.song_a:
            self.set_song_selection("A", self.song_a)
        if self.song_b:
            self.set_song_selection("B", self.song_b)

    def _clear_selection(self, role: str) -> None:
        self.set_song_selection(role, None)

    def _refresh_search(self) -> None:
        query = self.search_edit.text().strip().lower()
        keywords = query.split()

        def _match(song: Dict[str, Any]) -> bool:
            if not keywords:
                return True
            combined = f"{song.get('artist','')} {song.get('title','')} {song.get('album','')}".lower()
            return all(k in combined for k in keywords)

        filtered = [s for s in self.library if _match(s)]
        self.search_results.clear()
        for s in filtered[:300]:
            item = QtWidgets.QListWidgetItem(_format_search_row(s))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, s)
            self.search_results.addItem(item)
        self.status_lbl.setText(f"Results: {min(len(filtered), 300)} shown / {len(filtered)} total matches")

    def _set_from_selection(self, role: str) -> None:
        item = self.search_results.currentItem()
        if not item:
            return
        song = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(song, dict):
            return
        self.controller.set_harmonic_song(role, song)

    def _run_matching(self) -> None:
        mode = "key" if self.mode_checkbox.isChecked() else "bpm"
        tol = float(self.tolerance_spin.value())
        # Do not filter transitions by the search box; search is only for picking Song A/B
        filters = {}
        result = self.controller.run_harmonic_match(
            song_a=self.song_a,
            song_b=self.song_b,
            mode=mode,
            bpm_tolerance_pct=tol,
            filters=filters,
        )
        self._render_results(result)

    def _render_results(self, result: Dict[str, Any]) -> None:
        self._clear_results()
        errors = result.get("errors") or []
        if errors:
            self.status_lbl.setText("; ".join(errors))
            self.status_lbl.setVisible(True)
        else:
            self.status_lbl.setText("")
            self.status_lbl.setVisible(False)
        paths = result.get("paths") or []
        if not paths:
            return
        # Take the shortest-path result (first) for now
        self.current_path = paths[0]
        self.selected_by_hop = {}
        hops = (self.current_path or {}).get("hops") or []
        self._build_columns(hops)

    def _save_playlist(self) -> None:
        paths = self.controller.last_harmonic_result or []
        self.controller.save_harmonic_playlist(paths)
        self.status_lbl.setText("Playlist saved.")

    def _clear_playlist(self) -> None:
        self.controller.clear_harmonic_playlist()
        self.status_lbl.setText("Playlist cleared.")

    # --- Column rendering ---
    def _clear_results(self) -> None:
        self._clear_columns_ui()
        self.selected_by_hop = {}
        self.current_path = None
        self.column_widgets = {}

    def _clear_columns_ui(self) -> None:
        while self.columns_layout.count():
            item = self.columns_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.column_widgets = {}

    def _build_columns(self, hops: List[Dict[str, Any]]) -> None:
        self._clear_columns_ui()
        for idx, hop in enumerate(hops):
            col = self._build_column_widget(idx, hop, enabled=(idx == 0))
            self.columns_layout.addWidget(col)
        self.columns_layout.addStretch(1)

    def _build_column_widget(self, hop_index: int, hop: Dict[str, Any], enabled: bool) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(f"Hop {hop_index + 1}")
        v = QtWidgets.QVBoxLayout(box)
        listw = QtWidgets.QListWidget()
        listw.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        listw.itemClicked.connect(lambda _item, idx=hop_index, lw=listw: self._on_column_selection(idx, lw, force=True))
        listw.itemSelectionChanged.connect(lambda idx=hop_index, lw=listw: self._on_column_selection(idx, lw, force=False))
        if not enabled:
            placeholder = QtWidgets.QListWidgetItem("Select previous hop to load options")
            placeholder.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            listw.addItem(placeholder)
            listw.setEnabled(False)
        else:
            self._populate_column(listw, hop)
        v.addWidget(listw)
        self.column_widgets[hop_index] = listw
        return box

    def _populate_column(self, listw: QtWidgets.QListWidget, hop: Dict[str, Any]) -> None:
        listw.clear()
        for cand in hop.get("candidates") or []:
            item = QtWidgets.QListWidgetItem(self._format_candidate_line(cand))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, cand)
            listw.addItem(item)
        if listw.count() == 0:
            placeholder = QtWidgets.QListWidgetItem("No candidates")
            placeholder.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            listw.addItem(placeholder)

    def _format_candidate_line(self, cand: Dict[str, Any]) -> str:
        artist = str(cand.get("artist", "")).strip()
        title = str(cand.get("title", "")).strip()
        album = str(cand.get("album", "")).strip()
        base_title = f"{artist} - {title}".strip(" -")
        if album:
            base_title = f"{base_title} [{album}]" if base_title else album
        bpm_orig = cand.get("bpm")
        bpm_adj = cand.get("adjusted_bpm") or bpm_orig
        try:
            bpm_orig_txt = f"{float(bpm_orig):.1f}" if bpm_orig not in (None, "") else ""
        except Exception:
            bpm_orig_txt = str(bpm_orig or "")
        try:
            bpm_adj_txt = f"{float(bpm_adj):.1f}" if bpm_adj not in (None, "") else ""
        except Exception:
            bpm_adj_txt = str(bpm_adj or "")
        offset = cand.get("bpm_offset_pct") or cand.get("bpm_offset") or 0.0
        try:
            offset_txt = f"{float(offset):+.1f}%"
        except Exception:
            offset_txt = str(offset)
        key_base = cand.get("key_labels") or {}
        key_adj = cand.get("adjusted_key_labels") or key_base
        key_line = f"{key_base.get('open','')} -> {key_adj.get('open','')}" if key_base else ""
        bpm_line = " | ".join(p for p in [f"{bpm_orig_txt} -> {bpm_adj_txt} ({offset_txt})" if bpm_adj_txt else bpm_orig_txt, key_line] if p)
        return f"{base_title}\n{bpm_line}" if bpm_line else base_title

    def _on_column_selection(self, hop_index: int, listw: QtWidgets.QListWidget, force: bool = False) -> None:
        if not self.current_path:
            return
        items = listw.selectedItems()
        if not items:
            # deselect: clear downstream
            self._clear_downstream(hop_index)
            return
        cand = items[0].data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(cand, dict):
            return
        # Toggle off only on explicit click of the same item
        prev = self.selected_by_hop.get(hop_index)
        if force and (prev is cand or prev == cand):
            listw.clearSelection()
            self._clear_downstream(hop_index)
            self.selected_by_hop.pop(hop_index, None)
            return
        self.selected_by_hop[hop_index] = cand
        self._unlock_next_column(hop_index + 1)

    def _clear_downstream(self, from_index: int) -> None:
        # Clear selections and disable columns after from_index
        for i, lw in self.column_widgets.items():
            if i <= from_index:
                continue
            lw.clear()
            placeholder = QtWidgets.QListWidgetItem("Select previous hop to load options")
            placeholder.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            lw.addItem(placeholder)
            lw.setEnabled(False)
            self.selected_by_hop.pop(i, None)

    def _unlock_next_column(self, next_index: int) -> None:
        if not self.current_path:
            return
        hops = (self.current_path or {}).get("hops") or []
        if next_index >= len(hops):
            return
        lw = self.column_widgets.get(next_index)
        if lw is None:
            return
        lw.setEnabled(True)
        self._populate_column(lw, hops[next_index])
        lw.viewport().update()
        self.columns_container.adjustSize()
        self.columns_area.viewport().update()

    def _remove_first_hop(self) -> None:
        # Drop first hop selection and rebuild from hop1 as new path
        if not self.current_path:
            return
        hops = self.current_path.get("hops") or []
        if not hops:
            return
        remaining = hops[1:]
        self.current_path = {"hops": remaining}
        self.selected_by_hop = {}
        self._build_columns(remaining)

    def _reapply_current_bpm(self) -> None:
        # Re-run matching with current BPM anchor
        self._refresh_current_track_state()
        # Refresh selections to reflect new anchor BPM
        if self.song_a:
            self.set_song_selection("A", self.song_a)
        if self.song_b:
            self.set_song_selection("B", self.song_b)
        self._run_matching()

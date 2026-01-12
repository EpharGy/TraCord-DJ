"""Harmonic mixing helper utilities.

Finds harmonic transition chains between two songs using Open Key compatibility,
optionally considering BPM adjustment within a tolerance.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence

from utils.harmonic_keys import (
    get_compatible_open_keys,
    open_key_int_to_camelot,
    open_key_int_to_pitch,
    open_key_int_to_straight_key,
    open_key_int_to_str,
    shift_key_by_semitones,
)

SongRecord = Dict[str, Any]
FilterSpec = Dict[str, str]


def _normalize_bpm(value: Any) -> Optional[float]:
    try:
        bpm = float(value)
    except Exception:
        return None
    return bpm if bpm > 0 else None


def _normalize_key_int(value: Any) -> Optional[int]:
    try:
        key_int = int(value)
    except Exception:
        return None
    return key_int if 0 <= key_int < 24 else None


def describe_key(key_int: int) -> Dict[str, Optional[str]]:
    return {
        "open": open_key_int_to_str(key_int),
        "camelot": open_key_int_to_camelot(key_int),
        "straight": open_key_int_to_straight_key(key_int),
    }


def find_shortest_key_paths(start_key: int, target_key: int, *, max_depth: int = 5) -> List[List[int]]:
    if start_key is None or target_key is None:
        return []
    if start_key == target_key:
        return [[start_key]]

    paths: List[List[int]] = []
    queue: List[List[int]] = [[start_key]]
    best_depth: Dict[int, int] = {start_key: 0}

    while queue:
        path = queue.pop(0)
        last = path[-1]
        depth = len(path) - 1
        if depth >= max_depth:
            continue
        for nxt in get_compatible_open_keys(last):
            new_depth = depth + 1
            if best_depth.get(nxt, new_depth) < new_depth:
                continue
            best_depth[nxt] = new_depth
            new_path = path + [nxt]
            if nxt == target_key:
                paths.append(new_path)
            else:
                queue.append(new_path)

    if not paths:
        return []
    min_len = min(len(p) for p in paths)
    return [p for p in paths if len(p) == min_len]


def _match_filters(song: SongRecord, filters: FilterSpec) -> bool:
    if not filters:
        return True
    artist_q = filters.get("artist", "").strip().lower()
    title_q = filters.get("title", "").strip().lower()
    album_q = filters.get("album", "").strip().lower()
    combo_q = filters.get("query", "").strip().lower()

    def _contains(val: Any, query: str) -> bool:
        if not query:
            return True
        return query in str(val or "").lower()

    base_match = (
        _contains(song.get("artist"), artist_q)
        and _contains(song.get("title"), title_q)
        and _contains(song.get("album"), album_q)
    )
    if combo_q:
        combined = f"{song.get('artist','')} {song.get('title','')} {song.get('album','')}".lower()
        return base_match and all(q in combined for q in combo_q.split())
    return base_match


def _collect_by_key(songs: Iterable[SongRecord]) -> Dict[int, List[SongRecord]]:
    index: Dict[int, List[SongRecord]] = {}
    for song in songs:
        key_int = _normalize_key_int(song.get("musical_key"))
        if key_int is None:
            continue
        index.setdefault(key_int, []).append(song)
    return index


def _adjust_for_bpm(anchor_bpm: float, song_bpm: float, key_int: int, tolerance_pct: float) -> Optional[Dict[str, Any]]:
    if anchor_bpm <= 0 or song_bpm <= 0:
        return None
    ratio = anchor_bpm / song_bpm
    if ratio <= 0:
        return None
    if abs(ratio - 1.0) > (tolerance_pct / 100.0):
        return None
    adjusted_bpm = song_bpm * ratio
    semitone_shift = 12.0 * math.log2(max(ratio, 1e-9))
    adjusted_key_int = shift_key_by_semitones(key_int, semitone_shift) or key_int
    return {
        "ratio": ratio,
        "offset_pct": (ratio - 1.0) * 100.0,
        "adjusted_bpm": adjusted_bpm,
        "adjusted_key_int": adjusted_key_int,
    }


def build_harmonic_paths(
    *,
    song_a: SongRecord,
    song_b: SongRecord,
    library: Sequence[SongRecord],
    mode: str = "bpm",
    bpm_tolerance_pct: float = 5.0,
    filters: FilterSpec | None = None,
    max_depth: int = 5,
    anchor_bpm: float | None = None,
) -> Dict[str, Any]:
    """Compute harmonic transition chains.

    Returns a dict with keys: paths (list), meta (dict), and errors (list).
    """
    errors: List[str] = []
    filters = filters or {}

    a_bpm = _normalize_bpm(song_a.get("bpm"))
    b_bpm = _normalize_bpm(song_b.get("bpm"))
    a_key = _normalize_key_int(song_a.get("musical_key"))
    b_key = _normalize_key_int(song_b.get("musical_key"))

    if a_key is None or b_key is None:
        errors.append("Song A and B must have keys.")
        return {"paths": [], "meta": {}, "errors": errors}

    anchor = _normalize_bpm(anchor_bpm) or a_bpm or b_bpm
    if mode == "bpm" and anchor is None:
        errors.append("BPM-aware mode requires a BPM (from Song A, B, or anchor).")
        return {"paths": [], "meta": {}, "errors": errors}

    key_paths = find_shortest_key_paths(a_key, b_key, max_depth=max_depth)
    if not key_paths:
        errors.append("No harmonic key path found between Song A and Song B.")
        return {"paths": [], "meta": {}, "errors": errors}

    index = _collect_by_key(library)

    results = []
    for key_path in key_paths:
        hop_results = []
        valid_chain = True
        for hop_key in key_path[1:]:
            songs_for_key = [s for s in index.get(hop_key, []) if _match_filters(s, filters)]
            candidates = []
            for s in songs_for_key:
                bpm = _normalize_bpm(s.get("bpm"))
                base_payload: Dict[str, Any] = {
                    "artist": s.get("artist"),
                    "title": s.get("title"),
                    "album": s.get("album"),
                    "bpm": bpm,
                    "musical_key": hop_key,
                    "key_labels": describe_key(hop_key),
                }
                if mode == "bpm":
                    if anchor is None or bpm is None:
                        continue
                    adj = _adjust_for_bpm(anchor, bpm, hop_key, bpm_tolerance_pct)
                    if not adj:
                        continue
                    # Require adjusted key to match the hop key; otherwise skip this candidate
                    if adj.get("adjusted_key_int") is not None and adj.get("adjusted_key_int") != hop_key:
                        continue
                    adj_key_labels = describe_key(adj["adjusted_key_int"])
                    base_payload.update(
                        {
                            "bpm_offset_pct": adj["offset_pct"],
                            "adjusted_bpm": adj["adjusted_bpm"],
                            "adjusted_key_int": adj["adjusted_key_int"],
                            "adjusted_key_labels": adj_key_labels,
                        }
                    )
                candidates.append(base_payload)
            if not candidates:
                valid_chain = False
                break
            hop_results.append(
                {
                    "key_int": hop_key,
                    "labels": describe_key(hop_key),
                    "candidates": candidates,
                }
            )
        if valid_chain:
            results.append(
                {
                    "key_path": key_path,
                    "key_labels": [describe_key(k) for k in key_path],
                    "hops": hop_results,
                }
            )

    if not results:
        errors.append("No valid chains with available songs along the path.")

    meta = {
        "mode": mode,
        "bpm_tolerance_pct": bpm_tolerance_pct,
        "anchor_bpm": anchor,
        "key_paths": key_paths,
    }

    return {"paths": results, "meta": meta, "errors": errors}

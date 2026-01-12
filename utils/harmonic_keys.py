"""
Harmonic Key utilities for Traktor Open Key <-> int conversion and key compatibility.

Adds Camelot and straight-key (single-name) helpers to keep all notations in sync.
"""

# Traktor Open Key int to Open Key string mapping
OPEN_KEY_MAP = [
    "1d", "8d", "3d", "10d", "5d", "12d", "7d", "2d", "9d", "4d", "11d", "6d",
    "10m", "5m", "12m", "7m", "2m", "9m", "4m", "11m", "6m", "1m", "8m", "3m"
]

OPEN_KEY_STR_TO_INT = {k: i for i, k in enumerate(OPEN_KEY_MAP)}

# Camelot -> straight key (single-name) lookup. No enharmonic pairs.
CAMELOT_TO_STRAIGHT = {
    "1A": "Ab minor",
    "1B": "B major",
    "2A": "Eb minor",
    "2B": "F# major",
    "3A": "Bb minor",
    "3B": "Db major",
    "4A": "F minor",
    "4B": "Ab major",
    "5A": "C minor",
    "5B": "Eb major",
    "6A": "G minor",
    "6B": "Bb major",
    "7A": "D minor",
    "7B": "F major",
    "8A": "A minor",
    "8B": "C major",
    "9A": "E minor",
    "9B": "G major",
    "10A": "B minor",
    "10B": "D major",
    "11A": "F# minor",
    "11B": "A major",
    "12A": "C# minor",
    "12B": "E major",
}

NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

# Precompute pitch (semitone + mode) maps for conversions.
CAMELOT_TO_PITCH = {}
PITCH_TO_CAMELOT = {}
for code, label in CAMELOT_TO_STRAIGHT.items():
    note = label.split()[0].upper()
    mode = "major" if "major" in label.lower() else "minor"
    semitone = NOTE_TO_SEMITONE.get(note)
    if semitone is None:
        continue
    CAMELOT_TO_PITCH[code] = (semitone, mode)
    PITCH_TO_CAMELOT[(semitone, mode)] = code

def open_key_int_to_str(key_int):
    """Convert Traktor Open Key int to Open Key string (e.g., 9 -> '4d')."""
    if 0 <= key_int < 24:
        return OPEN_KEY_MAP[key_int]
    return "Unknown"

def open_key_str_to_int(key_str):
    """Convert Open Key string (e.g., '4d') to Traktor Open Key int."""
    return OPEN_KEY_STR_TO_INT.get(key_str.lower(), None)


def _normalize_open_key_number(num: int) -> int:
    # Clamp to 1..12 and wrap
    return ((num - 1) % 12) + 1


def open_key_to_camelot(key_str: str | None) -> str | None:
    """Convert Open Key (e.g., '8d'/'8m') to Camelot (e.g., '3B'/'3A').

    Mapping: Camelot number = open key number - 5 (wrap 1..12), d->B, m->A.
    Examples: 7d -> 2B, 8m -> 3A.
    """
    if not key_str:
        return None
    ks = key_str.strip().lower()
    if not ks:
        return None
    letter = ks[-1]
    if letter not in {"d", "m"}:
        return None
    try:
        num = int(ks[:-1])
    except Exception:
        return None
    if not 1 <= num <= 12:
        return None
    camelot_num = _normalize_open_key_number(num - 5)
    return f"{camelot_num}{'B' if letter == 'd' else 'A'}"


def open_key_int_to_camelot(key_int: int) -> str | None:
    """Convert Open Key int to Camelot (e.g., 1 -> '8B' when int maps to '8d')."""
    s = open_key_int_to_str(key_int)
    if s == "Unknown":
        return None
    return open_key_to_camelot(s)


def camelot_to_open_key_str(camelot: str | None) -> str | None:
    """Convert Camelot (e.g., '8B'/'8A') to Open Key string ('?d'/'?m').

    Mapping: Open key number = camelot number + 5 (wrap 1..12), B->d, A->m.
    """
    if not camelot:
        return None
    c = camelot.strip().upper()
    if not c:
        return None
    letter = c[-1]
    if letter not in {"A", "B"}:
        return None
    try:
        num = int(c[:-1])
    except Exception:
        return None
    if not 1 <= num <= 12:
        return None
    suffix = "m" if letter == "A" else "d"
    open_num = _normalize_open_key_number(num + 5)
    return f"{open_num}{suffix}"


def camelot_to_open_key_int(camelot: str | None) -> int | None:
    """Convert Camelot to Open Key int."""
    ok = camelot_to_open_key_str(camelot)
    if ok is None:
        return None
    return open_key_str_to_int(ok)


def camelot_to_straight_key(camelot: str | None) -> str | None:
    """Return straight key name (single-name, e.g., 'C major') for a Camelot code."""
    if not camelot:
        return None
    c = camelot.strip().upper()
    return CAMELOT_TO_STRAIGHT.get(c)


def open_key_int_to_straight_key(key_int: int) -> str | None:
    """Return straight key name for an Open Key int."""
    camelot = open_key_int_to_camelot(key_int)
    if camelot is None:
        return None
    return camelot_to_straight_key(camelot)


def open_key_str_to_straight_key(key_str: str | None) -> str | None:
    """Return straight key name for an Open Key string."""
    camelot = open_key_to_camelot(key_str) if key_str else None
    if camelot is None:
        return None
    return camelot_to_straight_key(camelot)


def camelot_to_pitch(camelot: str | None) -> tuple[int, str] | None:
    """Return (semitone, mode) for a Camelot code."""
    if not camelot:
        return None
    c = camelot.strip().upper()
    return CAMELOT_TO_PITCH.get(c)


def pitch_to_camelot(semitone: int, mode: str | None) -> str | None:
    """Return Camelot code for a (semitone, mode) pair."""
    try:
        st = int(semitone) % 12
    except Exception:
        return None
    m_norm = (mode or "").strip().lower()
    if m_norm not in {"major", "minor"}:
        return None
    return PITCH_TO_CAMELOT.get((st, m_norm))


def open_key_int_to_pitch(key_int: int) -> tuple[int, str] | None:
    """Return (semitone, mode) for an Open Key int."""
    camelot = open_key_int_to_camelot(key_int)
    if camelot is None:
        return None
    return camelot_to_pitch(camelot)


def shift_key_by_semitones(key_int: int, semitone_delta: float | int) -> int | None:
    """Shift an Open Key int by a semitone delta (rounded) and return a new Open Key int."""
    pitch = open_key_int_to_pitch(key_int)
    if pitch is None:
        return None
    semitone, mode = pitch
    try:
        delta = int(round(semitone_delta))
    except Exception:
        return None
    new_semitone = (semitone + delta) % 12
    camelot = pitch_to_camelot(new_semitone, mode)
    if camelot is None:
        return None
    return camelot_to_open_key_int(camelot)

def get_compatible_open_keys(key_int):
    """
    Given a Traktor Open Key int, return a list of compatible key ints (including self, +/-1, and relative minor/major).
    Wraps around the Camelot wheel as needed (1–12, A/B).
    """
    if not (0 <= key_int < 24):
        return []
    camelot = open_key_int_to_camelot(key_int)
    if not camelot:
        return []
    num = int(camelot[:-1])
    letter = camelot[-1]
    neighbors = []

    def _ok_to_int(c_code: str) -> int | None:
        return camelot_to_open_key_int(c_code)

    # Same key
    neighbors.append(key_int)
    # Relative (A<->B)
    rel = f"{num}{'B' if letter == 'A' else 'A'}"
    rel_int = _ok_to_int(rel)
    if rel_int is not None:
        neighbors.append(rel_int)
    # -1 and +1 with same letter (wrap 1..12)
    prev_num = 12 if num == 1 else num - 1
    next_num = 1 if num == 12 else num + 1
    for n in (prev_num, next_num):
        c_code = f"{n}{letter}"
        c_int = _ok_to_int(c_code)
        if c_int is not None:
            neighbors.append(c_int)
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for k in neighbors:
        if k not in seen:
            seen.add(k)
            ordered.append(k)
    return ordered

def get_compatible_open_key_strs(key_int):
    """
    Given a Traktor Open Key int, return a list of compatible Open Key strings.
    """
    return [open_key_int_to_str(i) for i in get_compatible_open_keys(key_int)]

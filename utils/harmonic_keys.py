"""
Harmonic Key utilities for Traktor Open Key <-> int conversion and key compatibility.
"""

# Traktor Open Key int to Open Key string mapping
OPEN_KEY_MAP = [
    "1d", "8d", "3d", "10d", "5d", "12d", "7d", "2d", "9d", "4d", "11d", "6d",
    "10m", "5m", "12m", "7m", "2m", "9m", "4m", "11m", "6m", "1m", "8m", "3m"
]

OPEN_KEY_STR_TO_INT = {k: i for i, k in enumerate(OPEN_KEY_MAP)}

def open_key_int_to_str(key_int):
    """Convert Traktor Open Key int to Open Key string (e.g., 9 -> '4d')."""
    if 0 <= key_int < 24:
        return OPEN_KEY_MAP[key_int]
    return "Unknown"

def open_key_str_to_int(key_str):
    """Convert Open Key string (e.g., '4d') to Traktor Open Key int."""
    return OPEN_KEY_STR_TO_INT.get(key_str.lower(), None)

def get_compatible_open_keys(key_int):
    """
    Given a Traktor Open Key int, return a list of compatible key ints (including self, +/-1, and relative minor/major).
    Wraps around the wheel as needed.
    """
    if not (0 <= key_int < 24):
        return []
    # Determine if major (d) or minor (m)
    is_major = key_int < 12
    base = key_int % 12
    # Same key
    compatible = [key_int]
    # -1 and +1 (wrap around)
    compatible.append((base - 1) % 12 + (0 if is_major else 12))
    compatible.append((base + 1) % 12 + (0 if is_major else 12))
    # Relative minor/major
    compatible.append((base + (12 if is_major else -12)) % 24)
    return compatible

def get_compatible_open_key_strs(key_int):
    """
    Given a Traktor Open Key int, return a list of compatible Open Key strings.
    """
    return [open_key_int_to_str(i) for i in get_compatible_open_keys(key_int)]

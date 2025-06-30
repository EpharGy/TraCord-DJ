import unicodedata

def normalize_string(s):
    """Normalize a string for robust matching: lowercase, strip, and NFKC unicode normalization."""
    if not isinstance(s, str):
        return ''
    s = unicodedata.normalize('NFKC', s)
    return s.casefold().strip()

def find_song_in_collection(artist, title, collection):
    """Find a song in the collection by normalized artist and title. Returns the matching dict or None."""
    norm_artist = normalize_string(artist)
    norm_title = normalize_string(title)
    for entry in collection:
        entry_artist = normalize_string(entry.get('artist', ''))
        entry_title = normalize_string(entry.get('title', ''))
        if entry_artist == norm_artist and entry_title == norm_title:
            return entry
    return None

def get_song_info(artist, title, collection):
    """Return the full dict from the collection if found, else a minimal dict."""
    match = find_song_in_collection(artist, title, collection)
    if match:
        return match  # Return the full song dict
    else:
        # Return a dict with all expected fields, but only artist/title filled
        return {
            'artist': artist,
            'title': title,
            'album': '',
            'genre': '',
            'bpm': '',
            'musical_key': '',
            'audio_file_path': ''
        }

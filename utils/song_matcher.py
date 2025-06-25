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
    """Return a dict with Artist, Title, and Album (if found) from the collection."""
    match = find_song_in_collection(artist, title, collection)
    if match:
        return {
            'artist': match.get('artist', artist),
            'title': match.get('title', title),
            'album': match.get('album', '')
        }
    else:
        return {
            'artist': artist,
            'title': title,
            'album': ''
        }

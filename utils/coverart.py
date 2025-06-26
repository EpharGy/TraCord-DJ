"""
Traktor Cover Art utilities: decompress and load cover art images from Traktor's Zstd-compressed files.
"""
import os
from typing import Optional, Any

try:
    import zstandard as zstd
    from PIL import Image
    import io
except ImportError:
    zstd = None
    Image = None
    io = None

def get_coverart_path(traktor_location: str, version_folder: str, coverart_id: str) -> str:
    """
    Build the full path to the cover art file given the Traktor root, version, and coverart string (e.g., '039/HNQ02OBHLMIWDCIJDEG0AVRGRPMB').
    """
    folder, filename = coverart_id.split("/")
    return os.path.join(traktor_location, version_folder, "Coverart", folder, filename + "000")


def decompress_coverart_file(filepath: str) -> Optional[bytes]:
    """
    Decompress a Traktor cover art file (Zstd) and return the raw image bytes (JPEG/PNG/etc).
    Returns None if zstandard is not installed or file is missing/corrupt.
    """
    if zstd is None:
        return None
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "rb") as f:
            dctx = zstd.ZstdDecompressor()
            return dctx.decompress(f.read())
    except Exception:
        return None


def load_coverart_image(image_bytes: bytes) -> Optional[Any]:  # Returns PIL.Image.Image or None
    """
    Load a PIL Image from decompressed image bytes.
    Returns None if Pillow is not installed or image is invalid.
    """
    if Image is None or io is None or not image_bytes:
        return None
    try:
        return Image.open(io.BytesIO(image_bytes))
    except Exception:
        return None


def get_coverart_image(traktor_location: str, version_folder: str, coverart_id: str) -> Optional[Any]:  # Returns PIL.Image.Image or None
    """
    High-level utility: get a PIL Image for a given coverart_id.
    Returns None if not available or on error.
    """
    path = get_coverart_path(traktor_location, version_folder, coverart_id)
    image_bytes = decompress_coverart_file(path)
    if image_bytes:
        return load_coverart_image(image_bytes)
    return None

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

from utils.logger import debug, info, warning, error

def get_coverart_path(traktor_location: str, version_folder: str, coverart_id: str) -> str:
    """
    Build the full path to the cover art file given the Traktor root, version, and coverart string (e.g., '039/HNQ02OBHLMIWDCIJDEG0AVRGRPMB').
    """
    folder, filename = coverart_id.split("/")
    path = os.path.join(traktor_location, version_folder, "Coverart", folder, filename + "000")
    debug(f"Cover art path resolved: {path}")
    return path


def decompress_coverart_file(filepath: str) -> Optional[bytes]:
    """
    Decompress a Traktor cover art file (Zstd) and return the raw image bytes (JPEG/PNG/etc).
    Returns None if zstandard is not installed or file is missing/corrupt.
    """
    if zstd is None:
        warning("zstandard module not installed; cannot decompress cover art.")
        return None
    if not os.path.exists(filepath):
        warning(f"Cover art file does not exist: {filepath}")
        return None
    try:
        with open(filepath, "rb") as f:
            dctx = zstd.ZstdDecompressor()
            decompressed = dctx.decompress(f.read())
            debug(f"Decompressed cover art file: {filepath} ({len(decompressed)} bytes)")
            return decompressed
    except Exception as e:
        error(f"Error decompressing cover art file {filepath}: {e}")
        return None


def load_coverart_image(image_bytes: bytes) -> Optional[Any]:  # Returns PIL.Image.Image or None
    """
    Load a PIL Image from decompressed image bytes.
    Returns None if Pillow is not installed or image is invalid.
    """
    if Image is None or io is None or not image_bytes:
        warning("Pillow or io not available, or image_bytes is empty; cannot load cover art image.")
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes))
        debug(f"Loaded cover art image: {img.format}, size={img.size}")
        return img
    except Exception as e:
        error(f"Error loading cover art image from bytes: {e}")
        return None


def get_coverart_image(traktor_location: str, version_folder: str, coverart_id: str) -> Optional[Any]:  # Returns PIL.Image.Image or None
    """
    High-level utility: get a PIL Image for a given coverart_id.
    Returns None if not available or on error.
    """
    info(f"Attempting to load cover art: location={traktor_location}, version={version_folder}, id={coverart_id}")
    path = get_coverart_path(traktor_location, version_folder, coverart_id)
    image_bytes = decompress_coverart_file(path)
    if image_bytes:
        return load_coverart_image(image_bytes)
    warning(f"No image bytes returned for cover art id: {coverart_id}")
    return None

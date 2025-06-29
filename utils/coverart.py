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

def load_coverart_image(image_bytes: bytes) -> Optional[Any]:  # Returns PIL.Image.Image or None
    """
    Load a PIL Image from decompressed image bytes.
    Returns None if Pillow is not installed or image is invalid.
    """
    if Image is None or io is None or not image_bytes:
        warning("[CoverArt] Pillow or io not available, or image_bytes is empty; cannot load cover art image.")
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes))
        info(f"[CoverArt] Loaded cover art image: {img.format}, size={img.size}")
        return img
    except Exception as e:
        error(f"[CoverArt] Error loading cover art image from bytes: {e}")
        return None

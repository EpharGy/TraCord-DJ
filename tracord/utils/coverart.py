"""Cover art extraction and transformation utilities.

This module centralizes logic for reading embedded artwork from audio files and
producing reusable image variants (GUI display, Spout output, base64 strings
for web overlays, etc.).
"""
from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from PIL import Image
from mutagen._file import File as MutagenFile
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from mutagen.mp3 import MP3

from utils.logger import get_logger

logger = get_logger(__name__)

SizeDict = Dict[str, Tuple[int, int]]


@dataclass(slots=True)
class CoverArtResult:
    """Represents the processed cover art assets for a track."""

    source_path: str
    original: Optional[Image.Image]
    variants: Dict[str, Image.Image]
    base64_png: Optional[str] = None

    @property
    def has_art(self) -> bool:
        return self.original is not None


def _extract_embedded_bytes(path: str) -> Optional[bytes]:
    """Return the first embedded artwork blob from *path*, if any."""

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".flac":
            audio = FLAC(path)
            if audio.pictures:
                return audio.pictures[0].data
        elif ext in {".mp3", ".m4a", ".aac", ".ogg"}:
            audio = MutagenFile(path)
            tags = getattr(audio, "tags", None) if audio else None
            if not audio or not tags:
                return None
            if ext == ".m4a" and "covr" in tags:
                covr = tags["covr"]
                if isinstance(covr, list) and covr:
                    return covr[0]
            if isinstance(audio, MP3) and isinstance(tags, ID3):
                for tag in tags.values():
                    if isinstance(tag, APIC):
                        return getattr(tag, "data", None)
            for tag in tags.values():
                if hasattr(tag, "data"):
                    return tag.data
                if isinstance(tag, bytes):
                    return tag
        else:
            audio = MutagenFile(path)
            if audio and getattr(audio, "pictures", None):
                return audio.pictures[0].data
    except Exception as exc:  # pragma: no cover - preventing crashes is critical
        logger.warning(f"[CoverArt] Failed to extract image bytes from {path}: {exc}")
    return None


def _load_image(data: bytes, source: Optional[str] = None) -> Optional[Image.Image]:
    try:
        with Image.open(io.BytesIO(data)) as img:
            converted = img.convert("RGBA")
        logger.debug(
            "[CoverArt] Loaded embedded image",
        )
        return converted
    except Exception as exc:  # pragma: no cover
        if source:
            logger.warning(f"[CoverArt] Invalid embedded image data for {source}: {exc}")
        else:
            logger.warning(f"[CoverArt] Invalid embedded image data: {exc}")
        return None


def load_cover_image(path: str) -> Optional[Image.Image]:
    """Return a PIL image for the first embedded artwork, or ``None``."""

    art_bytes = _extract_embedded_bytes(path)
    if not art_bytes:
        logger.warning(f"[CoverArt] No embedded artwork found: {path}")
        return None
    return _load_image(art_bytes, source=path)


def _resize(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """Return a resized copy using high-quality resampling."""

    try:  # Pillow >=9
        resample = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - legacy fallback
        resample = Image.LANCZOS  # type: ignore[attr-defined]
    return image.resize(size, resample).copy()


def _encode_png(image: Image.Image) -> str:
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")


def build_cover_art(
    path: str,
    *,
    sizes: SizeDict,
    base64_variant: Optional[str] = None,
) -> CoverArtResult:
    """Load artwork from *path* and prepare resized variants.

    Args:
        path: Absolute path to the audio file on disk.
        sizes: Mapping of variant name -> (width, height).
        base64_variant: Optional key inside *sizes* whose image should be encoded
            as PNG base64 for overlays.

    Returns:
        CoverArtResult. When no artwork exists, ``original`` is ``None`` and the
        variants/base64 are empty.
    """

    original = load_cover_image(path)
    if not original:
        return CoverArtResult(path, None, {}, None)

    variants: Dict[str, Image.Image] = {}
    for key, size in sizes.items():
        variants[key] = _resize(original, size)
        logger.debug(f"[CoverArt] Prepared variant '{key}' at {size}")

    base64_png = None
    if base64_variant and base64_variant in variants:
        base64_png = _encode_png(variants[base64_variant])

    return CoverArtResult(path, original, variants, base64_png)


def ensure_variants(
    path: str,
    *,
    sizes: SizeDict,
    base64_variant: Optional[str] = None,
) -> CoverArtResult:
    """Public helper that wraps :func:`build_cover_art` with logging."""

    result = build_cover_art(path, sizes=sizes, base64_variant=base64_variant)
    if not result.has_art:
        logger.debug(f"[CoverArt] No art assets generated for {path}")
    return result


def blank_image(size: Tuple[int, int], color=(0, 0, 0, 0)) -> Image.Image:
    """Return a transparent placeholder image for *size*."""

    return Image.new("RGBA", size, color)

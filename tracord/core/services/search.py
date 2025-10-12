"""Search backend abstraction for TraCord DJ."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from utils.traktor import load_collection_json, search_collection_json
from utils.logger import get_logger


logger = get_logger(__name__)


@dataclass(slots=True)
class SearchResult:
    matches: List[str]
    total_matches: int


class SearchBackend:
    """Base search backend interface."""

    def search(self, query: str, *, limit: Optional[int] = None) -> SearchResult:  # pragma: no cover - interface
        raise NotImplementedError

    def reload(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class JsonSearchBackend(SearchBackend):
    """Search backend operating on the exported collection JSON."""

    def __init__(self, collection_path: Path, *, default_limit: Optional[int] = None) -> None:
        self.collection_path = collection_path
        self.default_limit = default_limit
        self._songs: List[dict[str, Any]] = []
        self._collection_mtime: Optional[float] = None
        self.reload()

    def _needs_reload(self) -> bool:
        try:
            mtime = self.collection_path.stat().st_mtime
        except FileNotFoundError:
            if self._collection_mtime is not None:
                logger.warning(f"[Search] Collection file missing: {self.collection_path}")
            self._collection_mtime = None
            self._songs = []
            return False
        if self._collection_mtime is None or mtime > (self._collection_mtime or 0):
            self._collection_mtime = mtime
            return True
        return False

    def reload(self) -> None:
        if not self.collection_path.exists():
            logger.warning(f"[Search] Collection JSON not found at {self.collection_path}")
            self._songs = []
            self._collection_mtime = None
            return
        self._songs = load_collection_json(str(self.collection_path)) or []
        try:
            self._collection_mtime = self.collection_path.stat().st_mtime
        except FileNotFoundError:
            self._collection_mtime = None
        logger.debug(f"[Search] Loaded {len(self._songs)} songs from {self.collection_path}")

    def _ensure_loaded(self) -> None:
        if self._needs_reload():
            self.reload()

    def song_count(self) -> int:
        self._ensure_loaded()
        return len(self._songs)

    def search(self, query: str, *, limit: Optional[int] = None) -> SearchResult:
        self._ensure_loaded()
        effective_limit = limit if limit is not None else self.default_limit
        matches, total = search_collection_json(self._songs, query, max_songs=effective_limit)
        return SearchResult(matches=matches, total_matches=total)

    @classmethod
    def from_settings(cls, settings) -> "JsonSearchBackend":
        path = Path(getattr(settings, "COLLECTION_JSON_FILE", ""))
        default_limit = getattr(settings, "MAX_SONGS", None)
        return cls(path, default_limit=default_limit if default_limit else None)

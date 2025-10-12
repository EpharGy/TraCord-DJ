"""Stdlib logging configuration helpers for TraCord DJ."""
from __future__ import annotations

import logging
import os
from typing import Iterable, Optional

_DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    *,
    level: int | str = logging.INFO,
    handlers: Optional[Iterable[logging.Handler]] = None,
    rich: bool = False,
) -> None:
    """Configure the root logger.

    Args:
        level: Logging level (numeric or string).
        handlers: Custom handlers to attach. When ``None`` a default stream
            handler is used.
        rich: When true, attempt to use RichHandler if available.
    """

    logging.shutdown()
    root = logging.getLogger()
    root.handlers.clear()

    if isinstance(level, str):
        level = level.upper()
    root.setLevel(level)

    if handlers is None:
        handlers = [_build_default_handler(rich=rich)]

    for handler in handlers:
        root.addHandler(handler)

    logging.captureWarnings(True)


def _build_default_handler(*, rich: bool) -> logging.Handler:
    if rich:
        try:
            from rich.logging import RichHandler  # type: ignore

            handler = RichHandler(markup=True, show_path=False)
            handler.setFormatter(logging.Formatter("%(message)s"))
            return handler
        except Exception:  # pragma: no cover - fallback to stdlib
            pass
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT))
    return handler


def setup_for_environment() -> None:
    """Configure logging based on environment variables."""

    level = os.getenv("TRACORD_LOG_LEVEL", "INFO")
    use_rich = os.getenv("TRACORD_LOG_RICH", "0") not in {"0", "false", "False"}
    configure_logging(level=level, rich=use_rich)

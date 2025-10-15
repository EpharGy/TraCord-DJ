"""Stdlib logging configuration helpers for TraCord DJ."""
from __future__ import annotations

import logging
import os
import sys
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

    # Tame noisy third-party loggers by default (can be overridden via env)
    try:
        discord_level_env = os.getenv("TRACORD_LOG_DISCORD_LEVEL")
        if discord_level_env:
            try:
                discord_level = getattr(logging, discord_level_env.upper())
            except Exception:
                discord_level = logging.INFO
        else:
            # If global level is higher than DEBUG, quiet discord logs to WARNING
            discord_level = logging.WARNING if root.level > logging.DEBUG else root.level
        for name in ("discord", "discord.gateway"):
            logging.getLogger(name).setLevel(discord_level)
    except Exception:
        pass


def _build_default_handler(*, rich: bool) -> logging.Handler:
    if rich:
        try:
            from rich.logging import RichHandler  # type: ignore

            handler = RichHandler(markup=True, show_path=False)
            handler.setFormatter(logging.Formatter("%(message)s"))
            return handler
        except Exception:  # pragma: no cover - fallback to stdlib
            pass
    # Always anchor the stream handler to the original stdout so GUI rewrites
    # (which replace ``sys.stdout``) do not leave the handler with a closed/null stream.
    handler = logging.StreamHandler(stream=getattr(sys, "__stdout__", sys.stdout))
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT))
    return handler


def setup_for_environment() -> None:
    """Configure logging based on environment variables."""

    level = os.getenv("TRACORD_LOG_LEVEL", "INFO")
    use_rich = os.getenv("TRACORD_LOG_RICH", "0") not in {"0", "false", "False"}
    configure_logging(level=level, rich=use_rich)

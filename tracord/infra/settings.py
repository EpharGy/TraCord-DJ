"""Typed settings loader for TraCord DJ."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_SETTINGS_PATH = _DEFAULT_DATA_DIR / "settings.json"


class SettingsModel(BaseModel):
    discord_token: str = Field(alias="DISCORD_TOKEN")
    discord_bot_app_id: str = Field(alias="DISCORD_BOT_APP_ID")
    discord_bot_channel_ids: list[str] = Field(default_factory=list, alias="DISCORD_BOT_CHANNEL_IDS")
    discord_bot_admin_ids: list[str] = Field(default_factory=list, alias="DISCORD_BOT_ADMIN_IDS")
    discord_live_notification_roles: list[str] = Field(default_factory=list, alias="DISCORD_LIVE_NOTIFICATION_ROLES")
    traktor_location: str = Field(alias="TRAKTOR_LOCATION")
    traktor_collection_filename: str = Field(alias="TRAKTOR_COLLECTION_FILENAME")
    traktor_broadcast_port: int = Field(8001, alias="TRAKTOR_BROADCAST_PORT")
    new_songs_days: int = Field(7, alias="NEW_SONGS_DAYS")
    max_songs: int = Field(20, alias="MAX_SONGS")
    timeout: float = Field(45.0, alias="TIMEOUT")
    console_panel_width: int = Field(700, alias="CONSOLE_PANEL_WIDTH")
    cover_size: int = Field(200, alias="COVER_SIZE")
    fade_style: str = Field("fade", alias="FADE_STYLE")
    fade_frames: int = Field(30, alias="FADE_FRAMES")
    fade_duration: float = Field(1.0, alias="FADE_DURATION")
    spout_border_px: int = Field(256, alias="SPOUT_BORDER_PX")
    spout_cover_size: int = Field(1080, alias="SPOUT_COVER_SIZE")
    midi_device: Optional[str] = Field(None, alias="MIDI_DEVICE")
    debug: bool = Field(False, alias="DEBUG")
    excluded_items: Optional[Dict[str, list[str]]] = Field(None, alias="EXCLUDED_ITEMS")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


_cached_settings: Optional[SettingsModel] = None


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _apply_environment_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    overrides = {
        "DISCORD_TOKEN": os.getenv("TRACORD_DISCORD_TOKEN"),
        "TRAKTOR_LOCATION": os.getenv("TRACORD_TRAKTOR_LOCATION"),
        "TRAKTOR_COLLECTION_FILENAME": os.getenv("TRACORD_COLLECTION_FILENAME"),
    }
    return {**data, **{k: v for k, v in overrides.items() if v is not None}}


def load_settings(*, path: Path = _SETTINGS_PATH, force: bool = False) -> SettingsModel:
    global _cached_settings
    if _cached_settings is not None and not force:
        return _cached_settings

    data = _load_json(path)
    data = _apply_environment_overrides(data)
    _cached_settings = SettingsModel.parse_obj(data)
    return _cached_settings


def reload_settings(*, path: Path = _SETTINGS_PATH) -> SettingsModel:
    return load_settings(path=path, force=True)

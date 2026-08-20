"""Application settings manager."""
import json
import os
from pathlib import Path


_CONFIG_DIR = Path.home() / ".config" / "video_automator"
_CONFIG_FILE = _CONFIG_DIR / "settings.json"

_DEFAULTS = {
    "last_output_dir": str(Path.home() / "Videos"),
    "last_clip_duration": 60,
    "last_base_name": "clip",
    "include_partial_clip": True,
    "subtitle_mode": "no_subtitles",
    "overwrite_mode": "renumber",
    "ffmpeg_path": "",
    "ffprobe_path": "",
    "translation_api_key": "",
    "translation_provider": "",
    "window_width": 1100,
    "window_height": 760,
}


class AppSettings:
    """Load and persist user preferences using a JSON config file."""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        self._data = dict(_DEFAULTS)
        try:
            if _CONFIG_FILE.exists():
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
        except Exception:
            pass

    def save(self):
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    # Convenience properties
    @property
    def last_output_dir(self) -> str:
        return self.get("last_output_dir", str(Path.home() / "Videos"))

    @last_output_dir.setter
    def last_output_dir(self, value: str):
        self.set("last_output_dir", value)

    @property
    def ffmpeg_path(self) -> str:
        return self.get("ffmpeg_path", "")

    @property
    def ffprobe_path(self) -> str:
        return self.get("ffprobe_path", "")

    @property
    def translation_api_key(self) -> str:
        return self.get("translation_api_key", "")

    @property
    def translation_provider(self) -> str:
        return self.get("translation_provider", "")


# Singleton
_settings_instance = None


def get_settings() -> AppSettings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings()
    return _settings_instance

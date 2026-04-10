"""Application settings with JSON persistence."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ConflictPolicy(Enum):
    """Pre-batch policy for handling existing output files.

    Values:
        ASK: Prompt user for each file (single-file mode only).
        OVERWRITE_ALL: Overwrite all existing output files.
        SKIP_ALL: Skip files that already have output.
        RENAME_ALL: Auto-rename output files with suffix _1, _2, etc.
    """

    ASK = "ask"
    OVERWRITE_ALL = "overwrite_all"
    SKIP_ALL = "skip_all"
    RENAME_ALL = "rename_all"


class ConverterEngine(Enum):
    """Available converter engines for .ts to .mp4 conversion.

    Values:
        AVIDEMUX: Use Avidemux CLI for conversion (default).
        FFMPEG: Use FFmpeg for conversion.
    """

    AVIDEMUX = "avidemux"
    FFMPEG = "ffmpeg"


def _get_settings_dir() -> Path:
    """Get the settings directory path.

    Uses TS2MP4_SETTINGS_DIR env var if set (for testing),
    otherwise uses %APPDATA%/Ts2Mp4/.
    """
    env_dir = os.environ.get("TS2MP4_SETTINGS_DIR")
    if env_dir:
        return Path(env_dir)
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return Path(appdata) / "Ts2Mp4"
    return Path.home() / ".ts2mp4"


@dataclass
class AppSettings:
    """Application settings for the current session.

    Attributes:
        output_directory: Custom output directory (None = same as source).
        conflict_policy: Default file conflict resolution.
        auto_delete_source: Delete source .ts files after successful conversion.
        window_geometry: Window position and size (bytes as hex string for JSON).
        last_import_directory: Last used directory in file import dialog.
        converter_engine: Selected converter engine (default: Avidemux).
    """

    output_directory: Optional[str] = None
    conflict_policy: ConflictPolicy = ConflictPolicy.ASK
    auto_delete_source: bool = False
    window_geometry: Optional[str] = None
    last_import_directory: Optional[str] = None
    converter_engine: ConverterEngine = ConverterEngine.AVIDEMUX

    @property
    def output_path(self) -> Optional[Path]:
        """Return the output directory as a Path, or None for same-as-source."""
        if self.output_directory:
            return Path(self.output_directory)
        return None

    @property
    def last_import_path(self) -> Optional[Path]:
        """Return the last import directory as a Path."""
        if self.last_import_directory:
            return Path(self.last_import_directory)
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize settings to a dictionary for JSON storage."""
        return {
            "output_directory": self.output_directory,
            "conflict_policy": self.conflict_policy.value,
            "auto_delete_source": self.auto_delete_source,
            "window_geometry": self.window_geometry,
            "last_import_directory": self.last_import_directory,
            "converter_engine": self.converter_engine.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        """Deserialize settings from a dictionary.

        Args:
            data: Dictionary with settings values.

        Returns:
            A new AppSettings instance.
        """
        conflict_policy_str = data.get("conflict_policy", "ask")
        try:
            conflict_policy = ConflictPolicy(conflict_policy_str)
        except ValueError:
            conflict_policy = ConflictPolicy.ASK

        converter_engine_str = data.get("converter_engine", "avidemux")
        try:
            converter_engine = ConverterEngine(converter_engine_str)
        except ValueError:
            converter_engine = ConverterEngine.AVIDEMUX

        return cls(
            output_directory=data.get("output_directory"),
            conflict_policy=conflict_policy,
            auto_delete_source=data.get("auto_delete_source", False),
            window_geometry=data.get("window_geometry"),
            last_import_directory=data.get("last_import_directory"),
            converter_engine=converter_engine,
        )

    @classmethod
    def _settings_file_path(cls) -> Path:
        """Get the path to the settings JSON file."""
        settings_dir = _get_settings_dir()
        return settings_dir / "settings.json"

    def save(self) -> None:
        """Save settings to JSON file at %APPDATA%/Ts2Mp4/settings.json."""
        settings_file = self._settings_file_path()
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from JSON file, returning defaults if file doesn't exist.

        Returns:
            AppSettings loaded from file or defaults.
        """
        settings_file = cls._settings_file_path()
        if not settings_file.exists():
            return cls()

        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return cls()

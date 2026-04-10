"""Unit tests for AppSettings."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models.app_settings import AppSettings, ConflictPolicy, ConverterEngine


class TestConflictPolicy:
    """Tests for the ConflictPolicy enum."""

    def test_all_values_exist(self) -> None:
        """Verify all required conflict policy values are defined."""
        assert ConflictPolicy.ASK.value == "ask"
        assert ConflictPolicy.OVERWRITE_ALL.value == "overwrite_all"
        assert ConflictPolicy.SKIP_ALL.value == "skip_all"
        assert ConflictPolicy.RENAME_ALL.value == "rename_all"


class TestConverterEngine:
    """Tests for the ConverterEngine enum."""

    def test_all_values_exist(self) -> None:
        """Verify all required converter engine values are defined."""
        assert ConverterEngine.AVIDEMUX.value == "avidemux"
        assert ConverterEngine.FFMPEG.value == "ffmpeg"

    def test_default_is_avidemux(self) -> None:
        """Default settings should use Avidemux engine."""
        settings = AppSettings()
        assert settings.converter_engine == ConverterEngine.AVIDEMUX


class TestAppSettings:
    """Tests for the AppSettings dataclass."""

    def test_default_values(self) -> None:
        """Test AppSettings default values."""
        settings = AppSettings()
        assert settings.output_directory is None
        assert settings.conflict_policy == ConflictPolicy.ASK
        assert settings.auto_delete_source is False
        assert settings.window_geometry is None
        assert settings.last_import_directory is None
        assert settings.converter_engine == ConverterEngine.AVIDEMUX

    def test_output_path_property_none(self) -> None:
        """Test output_path returns None when no custom directory set."""
        settings = AppSettings()
        assert settings.output_path is None

    def test_output_path_property_set(self, tmp_path: Path) -> None:
        """Test output_path returns Path when custom directory set."""
        settings = AppSettings(output_directory=str(tmp_path))
        assert settings.output_path == tmp_path

    def test_last_import_path_property(self, tmp_path: Path) -> None:
        """Test last_import_path returns Path."""
        settings = AppSettings(last_import_directory=str(tmp_path))
        assert settings.last_import_path == tmp_path


class TestAppSettingsSerialization:
    """Tests for JSON serialization and deserialization."""

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        settings = AppSettings(
            output_directory="/some/path",
            conflict_policy=ConflictPolicy.OVERWRITE_ALL,
            auto_delete_source=True,
        )
        d = settings.to_dict()
        assert d["output_directory"] == "/some/path"
        assert d["conflict_policy"] == "overwrite_all"
        assert d["auto_delete_source"] is True
        assert d["converter_engine"] == "avidemux"

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "output_directory": "/custom/output",
            "conflict_policy": "skip_all",
            "auto_delete_source": True,
            "window_geometry": None,
            "last_import_directory": "/last/dir",
        }
        settings = AppSettings.from_dict(data)
        assert settings.output_directory == "/custom/output"
        assert settings.conflict_policy == ConflictPolicy.SKIP_ALL
        assert settings.auto_delete_source is True
        assert settings.last_import_directory == "/last/dir"

    def test_from_dict_invalid_conflict_policy(self) -> None:
        """Test that invalid conflict policy falls back to ASK."""
        data = {"conflict_policy": "invalid_value"}
        settings = AppSettings.from_dict(data)
        assert settings.conflict_policy == ConflictPolicy.ASK

    def test_from_dict_empty(self) -> None:
        """Test deserialization from empty dict returns defaults."""
        settings = AppSettings.from_dict({})
        assert settings.output_directory is None
        assert settings.conflict_policy == ConflictPolicy.ASK
        assert settings.auto_delete_source is False
        assert settings.converter_engine == ConverterEngine.AVIDEMUX

    def test_from_dict_with_converter_engine(self) -> None:
        """Test deserialization includes converter_engine."""
        data = {"converter_engine": "ffmpeg"}
        settings = AppSettings.from_dict(data)
        assert settings.converter_engine == ConverterEngine.FFMPEG

    def test_from_dict_missing_converter_engine_defaults_to_avidemux(self) -> None:
        """Test migration: missing converter_engine key defaults to avidemux."""
        data = {"output_directory": "/old/path", "conflict_policy": "ask"}
        settings = AppSettings.from_dict(data)
        assert settings.converter_engine == ConverterEngine.AVIDEMUX

    def test_from_dict_invalid_converter_engine_defaults_to_avidemux(self) -> None:
        """Test that invalid converter engine falls back to avidemux."""
        data = {"converter_engine": "invalid_engine"}
        settings = AppSettings.from_dict(data)
        assert settings.converter_engine == ConverterEngine.AVIDEMUX

    def test_round_trip(self) -> None:
        """Test serialization round-trip preserves data."""
        original = AppSettings(
            output_directory="/test/path",
            conflict_policy=ConflictPolicy.RENAME_ALL,
            auto_delete_source=True,
            last_import_directory="/import/dir",
        )
        restored = AppSettings.from_dict(original.to_dict())
        assert restored.output_directory == original.output_directory
        assert restored.conflict_policy == original.conflict_policy
        assert restored.auto_delete_source == original.auto_delete_source
        assert restored.last_import_directory == original.last_import_directory
        assert restored.converter_engine == original.converter_engine

    def test_round_trip_with_ffmpeg_engine(self) -> None:
        """Test round-trip preserves non-default converter engine."""
        original = AppSettings(converter_engine=ConverterEngine.FFMPEG)
        restored = AppSettings.from_dict(original.to_dict())
        assert restored.converter_engine == ConverterEngine.FFMPEG


class TestAppSettingsPersistence:
    """Tests for JSON file persistence."""

    def test_save_and_load(self) -> None:
        """Test saving to file and loading back."""
        settings = AppSettings(
            output_directory="/saved/path",
            conflict_policy=ConflictPolicy.SKIP_ALL,
            auto_delete_source=True,
        )
        settings.save()
        loaded = AppSettings.load()
        assert loaded.output_directory == "/saved/path"
        assert loaded.conflict_policy == ConflictPolicy.SKIP_ALL
        assert loaded.auto_delete_source is True

    def test_load_nonexistent_returns_defaults(self) -> None:
        """Test loading from nonexistent file returns default settings."""
        settings = AppSettings.load()
        assert settings.output_directory is None
        assert settings.conflict_policy == ConflictPolicy.ASK
        assert settings.auto_delete_source is False

    def test_load_corrupted_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test loading from corrupted JSON returns defaults."""
        settings_dir = tmp_path / "corrupt_settings"
        settings_dir.mkdir()
        monkeypatch.setenv("TS2MP4_SETTINGS_DIR", str(settings_dir))

        # Write corrupted JSON
        settings_file = settings_dir / "settings.json"
        settings_file.write_text("{invalid json content", encoding="utf-8")

        settings = AppSettings.load()
        assert settings.output_directory is None
        assert settings.conflict_policy == ConflictPolicy.ASK

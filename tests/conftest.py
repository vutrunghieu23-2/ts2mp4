"""Shared pytest fixtures for Ts2Mp4 tests."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest


SAMPLE_FILES_DIR = Path(__file__).parent / "sample_files"


@pytest.fixture
def sample_ts_path() -> Path:
    """Return path to the sample .ts test file."""
    path = SAMPLE_FILES_DIR / "sample.ts"
    if not path.exists():
        pytest.skip("Sample .ts file not found. Run FFmpeg to generate it first.")
    return path


@pytest.fixture
def tmp_ts_file(tmp_path: Path) -> Path:
    """Create a temporary fake .ts file for validation testing."""
    ts_file = tmp_path / "test_video.ts"
    ts_file.write_bytes(b"\x47" * 188)  # Single TS packet sync byte
    return ts_file


@pytest.fixture
def tmp_ts_files(tmp_path: Path) -> list[Path]:
    """Create multiple temporary fake .ts files for batch testing."""
    files = []
    for i in range(5):
        ts_file = tmp_path / f"video_{i}.ts"
        ts_file.write_bytes(b"\x47" * 188)
        files.append(ts_file)
    return files


@pytest.fixture
def tmp_non_ts_file(tmp_path: Path) -> Path:
    """Create a temporary non-.ts file for rejection testing."""
    other_file = tmp_path / "document.txt"
    other_file.write_text("Not a video file")
    return other_file


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def settings_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for settings file."""
    settings = tmp_path / "settings"
    settings.mkdir()
    return settings


@pytest.fixture(autouse=True)
def _isolate_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate AppSettings from real user settings during tests."""
    monkeypatch.setenv("TS2MP4_SETTINGS_DIR", str(tmp_path / "settings"))

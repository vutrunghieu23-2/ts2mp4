"""Unit tests for AvidemuxConverter."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.avidemux_converter import AvidemuxConverter
from src.models.conversion_job import ConversionJob


@pytest.fixture
def fake_avidemux(tmp_path: Path) -> Path:
    """Create a fake avidemux_cli.exe for testing."""
    binary = tmp_path / "avidemux_cli.exe"
    binary.write_text("fake binary")
    return binary


@pytest.fixture
def sample_job(tmp_path: Path) -> ConversionJob:
    """Create a sample conversion job for testing."""
    source = tmp_path / "video.ts"
    source.write_bytes(b"\x00" * 1024)
    output = tmp_path / "video.mp4"
    return ConversionJob.from_source(source, output_path=output)


class TestBuildCommand:
    """Tests for AvidemuxConverter.build_command()."""

    def test_command_has_correct_structure(
        self, fake_avidemux: Path, sample_job: ConversionJob
    ) -> None:
        """Build command should have the correct Avidemux CLI arguments."""
        converter = AvidemuxConverter(avidemux_path=fake_avidemux)
        cmd = converter.build_command(sample_job)

        assert cmd[0] == str(fake_avidemux)
        assert "--nogui" in cmd
        assert "--load" in cmd
        assert "--video-codec" in cmd
        assert "--audio-codec" in cmd
        assert "--output-format" in cmd
        assert "--save" in cmd
        assert "--quit" in cmd

    def test_command_uses_stream_copy(
        self, fake_avidemux: Path, sample_job: ConversionJob
    ) -> None:
        """Build command should use copy for both video and audio codecs."""
        converter = AvidemuxConverter(avidemux_path=fake_avidemux)
        cmd = converter.build_command(sample_job)

        video_idx = cmd.index("--video-codec")
        assert cmd[video_idx + 1] == "Copy"

        audio_idx = cmd.index("--audio-codec")
        assert cmd[audio_idx + 1] == "copy"

    def test_command_output_format_is_mp4(
        self, fake_avidemux: Path, sample_job: ConversionJob
    ) -> None:
        """Build command should set output format to mp4."""
        converter = AvidemuxConverter(avidemux_path=fake_avidemux)
        cmd = converter.build_command(sample_job)

        fmt_idx = cmd.index("--output-format")
        assert cmd[fmt_idx + 1] == "MP4"

    def test_command_input_path(
        self, fake_avidemux: Path, sample_job: ConversionJob
    ) -> None:
        """Build command should load the correct input file."""
        converter = AvidemuxConverter(avidemux_path=fake_avidemux)
        cmd = converter.build_command(sample_job)

        load_idx = cmd.index("--load")
        assert cmd[load_idx + 1] == str(sample_job.source_path)

    def test_command_output_path(
        self, fake_avidemux: Path, sample_job: ConversionJob
    ) -> None:
        """Build command should save to the correct output path."""
        converter = AvidemuxConverter(avidemux_path=fake_avidemux)
        cmd = converter.build_command(sample_job)

        save_idx = cmd.index("--save")
        assert cmd[save_idx + 1] == str(sample_job.output_path)

    def test_no_binary_raises_file_not_found(
        self, sample_job: ConversionJob
    ) -> None:
        """Build command should raise FileNotFoundError when binary is None."""
        converter = AvidemuxConverter(avidemux_path=None)
        with pytest.raises(FileNotFoundError, match="Avidemux CLI binary not found"):
            converter.build_command(sample_job)


class TestIsAvailable:
    """Tests for AvidemuxConverter.is_available()."""

    def test_available_when_path_exists(self, fake_avidemux: Path) -> None:
        """is_available() should return True when binary path is set."""
        converter = AvidemuxConverter(avidemux_path=fake_avidemux)
        assert converter.is_available() is True

    def test_not_available_when_path_is_none(self) -> None:
        """is_available() should return False when binary is None."""
        converter = AvidemuxConverter(avidemux_path=None)
        assert converter.is_available() is False


class TestConvertMissingBinary:
    """Tests for error handling when Avidemux binary is missing."""

    def test_convert_raises_file_not_found(
        self, sample_job: ConversionJob
    ) -> None:
        """convert() should raise FileNotFoundError with descriptive message."""
        converter = AvidemuxConverter(avidemux_path=None)
        gen = converter.convert(sample_job)
        with pytest.raises(FileNotFoundError) as exc_info:
            next(gen)
        assert "avidemux_cli.exe" in str(exc_info.value)
        assert "Settings" in str(exc_info.value)

    def test_get_process_returns_none_when_idle(self) -> None:
        """get_process() should return None when no conversion is running."""
        converter = AvidemuxConverter(avidemux_path=None)
        assert converter.get_process() is None

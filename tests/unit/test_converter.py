"""Unit tests for FFmpegConverter."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.converter import FFmpegConverter
from src.models.conversion_job import ConversionJob


class TestBuildCommand:
    """Tests for the FFmpeg command construction."""

    # --- Pass 1: Stream copy (default) ---

    def test_default_command_uses_stream_copy(self, tmp_ts_file: Path) -> None:
        """Test that default (pass 1) uses -c copy for maximum speed."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)
        cmd = converter.build_command(job)

        assert "-c" in cmd
        c_idx = cmd.index("-c")
        assert cmd[c_idx + 1] == "copy"
        # Should NOT have -c:v or -c:a in pass 1
        assert "-c:v" not in cmd
        assert "-c:a" not in cmd

    def test_default_command_structure(self, tmp_ts_file: Path) -> None:
        """Test that pass 1 command has all required flags."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)
        cmd = converter.build_command(job)

        assert cmd[0] == "ffmpeg.exe"
        assert "-i" in cmd
        assert str(tmp_ts_file) in cmd
        assert "-map" in cmd
        assert "0:v" in cmd
        assert "0:a" in cmd
        assert "-f" in cmd
        assert "mp4" in cmd
        assert "-movflags" in cmd
        assert "+faststart" in cmd
        assert "-y" in cmd

    # --- Pass 2: Audio re-encode ---

    def test_reencode_audio_command(self, tmp_ts_file: Path) -> None:
        """Test that reencode_audio=True uses -c:v copy and -c:a aac."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)
        cmd = converter.build_command(job, reencode_audio=True)

        # Should have separate video/audio codec flags
        cv_idx = cmd.index("-c:v")
        assert cmd[cv_idx + 1] == "copy"
        ca_idx = cmd.index("-c:a")
        assert cmd[ca_idx + 1] == "aac"
        ba_idx = cmd.index("-b:a")
        assert cmd[ba_idx + 1] == "128k"
        # Should NOT have generic -c copy
        assert "-c" not in cmd or cmd[cmd.index("-c") + 1] != "copy" if "-c" in cmd else True

    def test_reencode_audio_no_generic_copy(self, tmp_ts_file: Path) -> None:
        """Test that reencode_audio=True does not include generic -c copy."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)
        cmd = converter.build_command(job, reencode_audio=True)

        # Find all "-c" entries that are NOT "-c:v" or "-c:a"
        generic_c = [
            i for i, x in enumerate(cmd)
            if x == "-c" and cmd[i + 1] == "copy"
        ]
        assert len(generic_c) == 0, "Should not have generic -c copy in reencode mode"

    # --- Common flags (both passes) ---

    def test_command_has_correct_stream_selection(self, tmp_ts_file: Path) -> None:
        """Test -map 0:v -map 0:a for video and audio stream selection."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)

        for reencode in (False, True):
            cmd = converter.build_command(job, reencode_audio=reencode)
            map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
            assert len(map_indices) == 2
            assert cmd[map_indices[0] + 1] == "0:v"
            assert cmd[map_indices[1] + 1] == "0:a"

    def test_command_has_error_tolerance_flags(self, tmp_ts_file: Path) -> None:
        """Test that error tolerance flags are present in both passes."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)

        for reencode in (False, True):
            cmd = converter.build_command(job, reencode_audio=reencode)

            err_idx = cmd.index("-err_detect")
            assert cmd[err_idx + 1] == "ignore_err"

            ff_idx = cmd.index("-fflags")
            assert cmd[ff_idx + 1] == "+genpts+discardcorrupt"

            # Both must appear before -i
            i_idx = cmd.index("-i")
            assert err_idx < i_idx
            assert ff_idx < i_idx

    def test_command_has_max_muxing_queue(self, tmp_ts_file: Path) -> None:
        """Test that -max_muxing_queue_size is set in both passes."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)

        for reencode in (False, True):
            cmd = converter.build_command(job, reencode_audio=reencode)
            mq_idx = cmd.index("-max_muxing_queue_size")
            assert cmd[mq_idx + 1] == "1024"

    def test_command_output_path(self, tmp_ts_file: Path) -> None:
        """Test that the output path is the last argument."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        job = ConversionJob.from_source(tmp_ts_file)

        for reencode in (False, True):
            cmd = converter.build_command(job, reencode_audio=reencode)
            assert cmd[-1] == str(job.output_path)

    # --- Error handling ---

    def test_no_ffmpeg_raises_error(self, tmp_ts_file: Path) -> None:
        """Test that missing FFmpeg raises FileNotFoundError."""
        converter = FFmpegConverter(ffmpeg_path=None)
        job = ConversionJob.from_source(tmp_ts_file)

        with pytest.raises(FileNotFoundError, match="FFmpeg binary not found"):
            converter.build_command(job)

    def test_custom_output_path(self, tmp_ts_file: Path, tmp_path: Path) -> None:
        """Test command with custom output path."""
        converter = FFmpegConverter(ffmpeg_path=Path("ffmpeg.exe"))
        custom_output = tmp_path / "custom" / "output.mp4"
        job = ConversionJob.from_source(tmp_ts_file, output_path=custom_output)
        cmd = converter.build_command(job)

        assert cmd[-1] == str(custom_output)

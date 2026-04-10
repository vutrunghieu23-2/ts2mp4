"""Integration test for end-to-end conversion with real FFmpeg."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.converter import FFmpegConverter
from src.core.progress_parser import ProgressParser
from src.models.conversion_job import ConversionJob
from src.utils.paths import resolve_ffmpeg_path


# Skip all tests in this module if FFmpeg is not available
pytestmark = pytest.mark.skipif(
    resolve_ffmpeg_path() is None,
    reason="FFmpeg not found on system",
)


class TestEndToEndConversion:
    """End-to-end conversion tests using real FFmpeg."""

    def test_convert_sample_file(self, sample_ts_path: Path, tmp_output_dir: Path) -> None:
        """Test actual conversion of sample.ts to .mp4."""
        output_path = tmp_output_dir / "sample.mp4"
        job = ConversionJob.from_source(sample_ts_path, output_path=output_path)

        converter = FFmpegConverter()
        lines = list(converter.convert(job))

        # Check output exists and has content
        assert output_path.exists(), f"Output file was not created: {output_path}"
        assert output_path.stat().st_size > 0, "Output file is empty"

    def test_probe_duration(self, sample_ts_path: Path) -> None:
        """Test probing duration of sample file."""
        parser = ProgressParser()
        duration = parser.probe_duration(sample_ts_path)

        assert duration is not None
        assert duration > 0

    def test_conversion_preserves_streams(
        self, sample_ts_path: Path, tmp_output_dir: Path
    ) -> None:
        """Test that conversion produces valid mp4 with video and audio."""
        import subprocess
        import json

        output_path = tmp_output_dir / "streams_test.mp4"
        job = ConversionJob.from_source(sample_ts_path, output_path=output_path)

        converter = FFmpegConverter()
        list(converter.convert(job))

        assert output_path.exists()

        # Probe output streams
        from src.utils.paths import resolve_ffprobe_path
        ffprobe = resolve_ffprobe_path()
        if ffprobe is None:
            pytest.skip("ffprobe not found")

        result = subprocess.run(
            [str(ffprobe), "-v", "quiet", "-print_format", "json", "-show_streams",
             str(output_path)],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        streams = data.get("streams", [])

        # Should have at least video stream
        stream_types = [s.get("codec_type") for s in streams]
        assert "video" in stream_types, f"No video stream found. Streams: {stream_types}"

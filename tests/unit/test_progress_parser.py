"""Unit tests for ProgressParser."""
from __future__ import annotations

import pytest

from src.core.progress_parser import ProgressParser


class TestParseProgress:
    """Tests for parsing FFmpeg progress lines."""

    def test_parse_time_format(self) -> None:
        """Test parsing time=HH:MM:SS.ms from FFmpeg stderr."""
        line = "frame=  100 fps=0.0 q=-1.0 size=   7424kB time=00:00:10.00 bitrate=6082.6kbits/s speed=20.0x"
        result = ProgressParser.parse_progress(line, total_duration=60.0)
        assert result is not None
        assert abs(result - (10.0 / 60.0 * 100)) < 0.1

    def test_parse_near_end(self) -> None:
        """Test parsing near the end of conversion."""
        line = "frame=  500 fps=25.0 time=00:01:00.00 bitrate=5000kbits/s speed=5.0x"
        result = ProgressParser.parse_progress(line, total_duration=60.0)
        assert result is not None
        assert abs(result - 100.0) < 0.1

    def test_parse_midpoint(self) -> None:
        """Test parsing at the midpoint."""
        line = "frame=  250 fps=25.0 time=00:00:30.00 bitrate=5000kbits/s speed=5.0x"
        result = ProgressParser.parse_progress(line, total_duration=60.0)
        assert result is not None
        assert abs(result - 50.0) < 0.1

    def test_parse_no_time_returns_none(self) -> None:
        """Test that lines without time= return None."""
        line = "FFmpeg version n5.1-1234 Copyright (c) 2000-2026 the FFmpeg developers"
        result = ProgressParser.parse_progress(line, total_duration=60.0)
        assert result is None

    def test_parse_none_duration_returns_none(self) -> None:
        """Test that None duration returns None."""
        line = "time=00:00:10.00"
        result = ProgressParser.parse_progress(line, total_duration=None)
        assert result is None

    def test_parse_zero_duration_returns_none(self) -> None:
        """Test that zero duration returns None."""
        line = "time=00:00:10.00"
        result = ProgressParser.parse_progress(line, total_duration=0.0)
        assert result is None

    def test_progress_never_exceeds_100(self) -> None:
        """Test that progress is capped at 100%."""
        line = "time=00:02:00.00"  # 120 seconds
        result = ProgressParser.parse_progress(line, total_duration=60.0)
        assert result is not None
        assert result == 100.0

    def test_parse_hours_format(self) -> None:
        """Test parsing with hours in the time."""
        line = "time=01:30:00.00"  # 1.5 hours = 5400 seconds
        result = ProgressParser.parse_progress(line, total_duration=7200.0)  # 2 hours
        assert result is not None
        assert abs(result - 75.0) < 0.1

    def test_parse_milliseconds(self) -> None:
        """Test parsing with fractional seconds."""
        line = "time=00:00:15.50"
        result = ProgressParser.parse_progress(line, total_duration=31.0)
        assert result is not None
        assert abs(result - 50.0) < 0.5


class TestParseTimeSeconds:
    """Tests for extracting time position in seconds."""

    def test_simple_time(self) -> None:
        """Test extracting seconds from simple time."""
        result = ProgressParser.parse_time_seconds("time=00:00:10.00")
        assert result is not None
        assert abs(result - 10.0) < 0.001

    def test_hours_minutes_seconds(self) -> None:
        """Test extracting time with hours and minutes."""
        result = ProgressParser.parse_time_seconds("time=01:30:45.50")
        assert result is not None
        expected = 1 * 3600 + 30 * 60 + 45.50
        assert abs(result - expected) < 0.001

    def test_no_match_returns_none(self) -> None:
        """Test that non-matching lines return None."""
        result = ProgressParser.parse_time_seconds("no time here")
        assert result is None

"""Unit tests for converter factory."""
from __future__ import annotations

import pytest

from src.core.avidemux_converter import AvidemuxConverter
from src.core.converter import FFmpegConverter
from src.core.converter_factory import create_converter
from src.models.app_settings import ConverterEngine


class TestCreateConverter:
    """Tests for create_converter() factory function."""

    def test_avidemux_engine_returns_avidemux_converter(self) -> None:
        """Factory should return AvidemuxConverter for AVIDEMUX engine."""
        converter = create_converter(ConverterEngine.AVIDEMUX)
        assert isinstance(converter, AvidemuxConverter)

    def test_ffmpeg_engine_returns_ffmpeg_converter(self) -> None:
        """Factory should return FFmpegConverter for FFMPEG engine."""
        converter = create_converter(ConverterEngine.FFMPEG)
        assert isinstance(converter, FFmpegConverter)

    def test_invalid_engine_raises_value_error(self) -> None:
        """Factory should raise ValueError for unknown engine values."""
        with pytest.raises(ValueError, match="Unknown converter engine"):
            create_converter("invalid_engine")  # type: ignore[arg-type]

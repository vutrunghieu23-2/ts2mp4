"""Converter factory — creates the appropriate converter based on engine selection."""
from __future__ import annotations

from src.core.avidemux_converter import AvidemuxConverter
from src.core.converter import ConverterProtocol, FFmpegConverter
from src.models.app_settings import ConverterEngine


def create_converter(engine: ConverterEngine) -> ConverterProtocol:
    """Create a converter instance for the given engine.

    Args:
        engine: The selected converter engine.

    Returns:
        A converter implementing ConverterProtocol.

    Raises:
        ValueError: If the engine value is not recognized.
    """
    if engine == ConverterEngine.AVIDEMUX:
        return AvidemuxConverter()
    elif engine == ConverterEngine.FFMPEG:
        return FFmpegConverter()
    else:
        raise ValueError(f"Unknown converter engine: {engine}")

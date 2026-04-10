"""Path resolution utilities for FFmpeg, Avidemux, and output files."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from src.models.app_settings import AppSettings


def resolve_ffmpeg_path() -> Optional[Path]:
    """Resolve the FFmpeg binary path.

    Search order per research.md R5:
    1. <app_dir>/ffmpeg/ffmpeg.exe (bundled)
    2. System PATH as fallback
    3. If neither found -> return None

    Returns:
        Path to ffmpeg.exe if found, None otherwise.
    """
    # 1. Check bundled location (next to exe for frozen, project root for dev)
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent.parent.parent  # src/utils -> src -> project root

    bundled_path = app_dir / "ffmpeg" / "ffmpeg.exe"
    if bundled_path.exists():
        return bundled_path

    # 2. Check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return Path(system_ffmpeg)

    # 3. Not found
    return None


def resolve_ffprobe_path() -> Optional[Path]:
    """Resolve the ffprobe binary path.

    Same search order as resolve_ffmpeg_path().

    Returns:
        Path to ffprobe.exe if found, None otherwise.
    """
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent.parent.parent

    bundled_path = app_dir / "ffmpeg" / "ffprobe.exe"
    if bundled_path.exists():
        return bundled_path

    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return Path(system_ffprobe)

    return None


def resolve_avidemux_path() -> Optional[Path]:
    """Resolve the Avidemux CLI binary path.

    Search order (mirrors resolve_ffmpeg_path):
    1. <app_dir>/avidemux/avidemux_cli.exe (bundled)
    2. System PATH as fallback
    3. If neither found -> return None

    Returns:
        Path to avidemux_cli.exe if found, None otherwise.
    """
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent.parent.parent

    bundled_path = app_dir / "avidemux" / "avidemux_cli.exe"
    if bundled_path.exists():
        return bundled_path

    system_avidemux = shutil.which("avidemux_cli")
    if system_avidemux:
        return Path(system_avidemux)

    return None


def resolve_output_path(source_path: Path, settings: AppSettings) -> Path:
    """Resolve the output .mp4 path for a given source .ts file.

    Rules per data-model.md:
    - If custom output directory is set: <custom_dir>/<source_basename>.mp4
    - If no custom directory (default): <source_dir>/<source_basename>.mp4

    Args:
        source_path: Path to the source .ts file.
        settings: Current application settings.

    Returns:
        The resolved output Path.
    """
    mp4_filename = source_path.stem + ".mp4"

    custom_dir = settings.output_path
    if custom_dir is not None:
        return custom_dir / mp4_filename
    else:
        return source_path.parent / mp4_filename


def resolve_conflict_path(output_path: Path) -> Path:
    """Resolve a unique output path when the target already exists.

    Appends _1, _2, etc. until a unique filename is found.
    Example: video.mp4 -> video_1.mp4 -> video_2.mp4

    Args:
        output_path: The original output path that conflicts.

    Returns:
        A unique path that does not exist.
    """
    if not output_path.exists():
        return output_path

    stem = output_path.stem
    suffix = output_path.suffix
    parent = output_path.parent

    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

"""FFmpeg progress output parser."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger
from src.utils.paths import resolve_ffprobe_path


# Pattern to match 'time=HH:MM:SS.ms' in FFmpeg stderr
_TIME_PATTERN = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")


class ProgressParser:
    """Parses FFmpeg stderr output for conversion progress.

    Uses ffprobe to determine total duration, then tracks the 'time='
    output from FFmpeg during conversion to calculate percentage.
    """

    def __init__(self, ffprobe_path: Optional[Path] = None) -> None:
        self._ffprobe_path = ffprobe_path or resolve_ffprobe_path()
        self._logger = get_logger()

    def probe_duration(self, path: Path) -> Optional[float]:
        """Get the duration of a media file using ffprobe.

        Args:
            path: Path to the media file.

        Returns:
            Duration in seconds, or None if probing fails.
        """
        if self._ffprobe_path is None:
            return None

        try:
            result = subprocess.run(
                [
                    str(self._ffprobe_path),
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    str(path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )

            if result.returncode != 0:
                return None

            # Guard against None/empty stdout (can happen with
            # network paths or inaccessible files on Windows)
            if not result.stdout:
                self._logger.warning(f"ffprobe returned empty output for {path}")
                return None

            data = json.loads(result.stdout)
            duration_str = data.get("format", {}).get("duration")
            if duration_str:
                return float(duration_str)
            return None

        except (subprocess.TimeoutExpired, json.JSONDecodeError, TypeError, OSError, ValueError) as e:
            self._logger.warning(f"Failed to probe duration for {path}: {e}")
            return None

    @staticmethod
    def parse_progress(stderr_line: str, total_duration: Optional[float]) -> Optional[float]:
        """Parse a single FFmpeg stderr line for progress percentage.

        Extracts 'time=HH:MM:SS.ms' and calculates percentage based
        on the known total duration.

        Args:
            stderr_line: A single line from FFmpeg stderr.
            total_duration: Total file duration in seconds.

        Returns:
            Progress percentage (0.0-100.0) if parseable, None otherwise.
        """
        if total_duration is None or total_duration <= 0:
            return None

        match = _TIME_PATTERN.search(stderr_line)
        if not match:
            return None

        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        current_time = hours * 3600 + minutes * 60 + seconds

        percentage = min(100.0, (current_time / total_duration) * 100.0)
        return percentage

    @staticmethod
    def parse_time_seconds(stderr_line: str) -> Optional[float]:
        """Extract the current time position from an FFmpeg stderr line.

        Args:
            stderr_line: A single line from FFmpeg stderr.

        Returns:
            Current position in seconds, or None if not found.
        """
        match = _TIME_PATTERN.search(stderr_line)
        if not match:
            return None

        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds

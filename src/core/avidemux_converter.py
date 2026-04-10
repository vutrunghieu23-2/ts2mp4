"""Avidemux CLI converter — subprocess wrapper for .ts to .mp4 remuxing.

Uses avidemux_cli.exe with stream copy (--video-codec copy --audio-codec copy)
to remux .ts files into .mp4 containers. Unlike FFmpegConverter, this is a
single-pass converter with no automatic retry strategy.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Generator, Optional

from src.models.conversion_job import ConversionJob
from src.utils.logger import get_logger
from src.utils.paths import resolve_avidemux_path


class AvidemuxConverter:
    """Wraps Avidemux CLI subprocess for .ts -> .mp4 conversion.

    Single-pass conversion via stream copy (remuxing). No re-encoding.
    If conversion fails, the file is marked as Error — no automatic retry.

    Command pattern:
        avidemux_cli.exe --nogui --load <input> --video-codec Copy
                         --audio-codec copy --output-format MP4
                         --save <output> --quit

    IMPORTANT: Avidemux CLI uses "Copy" (capital C) for video codec
    and "copy" (lowercase) for audio codec. Using wrong casing causes
    re-encoding instead of stream copy, resulting in very slow conversion.
    """

    _UNSET = object()  # Sentinel for auto-resolution

    def __init__(self, avidemux_path: Optional[Path] | object = _UNSET) -> None:
        """Initialize with optional Avidemux CLI path.

        Args:
            avidemux_path: Path to avidemux_cli.exe. If not provided, auto-resolves.
                          Pass None explicitly to indicate Avidemux is unavailable.
        """
        if avidemux_path is AvidemuxConverter._UNSET:
            self._avidemux_path = resolve_avidemux_path()
        else:
            self._avidemux_path = avidemux_path  # type: ignore[assignment]
        self._current_process: Optional[subprocess.Popen[bytes]] = None
        self._logger = get_logger()

    def build_command(self, job: ConversionJob) -> list[str]:
        """Build the Avidemux CLI command for a conversion job.

        Args:
            job: The ConversionJob with source and output paths.

        Returns:
            List of command arguments.

        Raises:
            FileNotFoundError: If Avidemux binary is not available.
        """
        if self._avidemux_path is None:
            raise FileNotFoundError(
                "Avidemux CLI binary not found. "
                "Please place avidemux_cli.exe in the avidemux/ directory "
                "or switch to FFmpeg engine in Settings."
            )

        return [
            str(self._avidemux_path),
            "--nogui",
            "--load", str(job.source_path),
            "--video-codec", "Copy",
            "--audio-codec", "copy",
            "--output-format", "MP4",
            "--save", str(job.output_path),
            "--quit",
        ]

    def convert(
        self, job: ConversionJob
    ) -> Generator[str, None, bool]:
        """Run Avidemux conversion (single pass, stream copy).

        This is a generator that yields each line from Avidemux's output.
        Since Avidemux CLI does not reliably output parseable progress,
        the caller should use indeterminate progress display.

        Args:
            job: The ConversionJob to convert.

        Yields:
            Lines from Avidemux stdout/stderr output.

        Returns:
            True if conversion succeeded, False otherwise.

        Raises:
            FileNotFoundError: If Avidemux binary is not available.
        """
        cmd = self.build_command(job)
        self._logger.info(
            f"Starting Avidemux conversion: {job.source_path} -> {job.output_path} "
            f"(size: {job.file_size} bytes)"
        )

        # Ensure output directory exists
        job.output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # IMPORTANT: Use stderr=subprocess.STDOUT to merge both streams.
            # Avidemux outputs hundreds of lines to stderr (plugin loading,
            # indexing progress, etc.). Using separate PIPEs for stdout and
            # stderr causes a DEADLOCK when the stderr buffer fills up (~65KB)
            # while we're blocked reading stdout.
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0
                ),
            )

            self._current_process = process

            # Read merged stdout+stderr line by line
            if process.stdout:
                for raw_line in process.stdout:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if line:
                        yield line

            process.wait()

            # Check success: return code 0 AND output file exists with size > 0
            success = (
                process.returncode == 0
                and job.output_path.exists()
                and job.output_path.stat().st_size > 0
            )

            if success:
                self._logger.info(
                    f"Avidemux conversion completed: {job.output_path}"
                )
                self._cleanup_idx2(job.source_path)
            else:
                self._logger.warning(
                    f"Avidemux conversion failed "
                    f"(exit code {process.returncode}): {job.source_path}"
                )

            return success

        except FileNotFoundError:
            self._logger.error(f"Avidemux not found: {self._avidemux_path}")
            raise
        except OSError as e:
            self._logger.error(f"OS error during Avidemux conversion: {e}")
            return False
        finally:
            self._current_process = None

    def _cleanup_idx2(self, source_path: Path) -> None:
        """Delete the .idx2 index file that Avidemux creates next to the source.

        Avidemux generates a <filename>.idx2 index file in the same directory
        as the input file during conversion. This method removes it after
        a successful conversion to keep the filesystem clean.
        """
        idx2_path = source_path.with_suffix(source_path.suffix + ".idx2")
        try:
            if idx2_path.exists():
                idx2_path.unlink()
                self._logger.info(f"Cleaned up index file: {idx2_path}")
        except OSError as e:
            self._logger.warning(f"Failed to delete index file {idx2_path}: {e}")

    def get_process(self) -> Optional[subprocess.Popen[bytes]]:
        """Get the currently running Avidemux process, if any."""
        return self._current_process

    def is_available(self) -> bool:
        """Check if the Avidemux CLI binary exists and is usable."""
        return self._avidemux_path is not None

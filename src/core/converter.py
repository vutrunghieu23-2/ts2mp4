"""Converter protocol and FFmpeg converter implementation.

Defines the ConverterProtocol interface and provides the FFmpegConverter
implementation with a two-pass strategy:
  Pass 1 (fast):   -c copy with error tolerance flags
  Pass 2 (robust): -c:v copy -c:a aac (re-encode audio only)

This ensures clean files convert at maximum speed (~1000x+), while
corrupt .ts files are automatically retried with audio re-encoding
to bypass aac_adtstoasc bitstream filter failures.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Generator, Optional, Protocol, runtime_checkable

from src.models.conversion_job import ConversionJob
from src.utils.logger import get_logger
from src.utils.paths import resolve_ffmpeg_path


@runtime_checkable
class ConverterProtocol(Protocol):
    """Common interface for converter implementations.

    Both FFmpegConverter and AvidemuxConverter implement this protocol.
    The ConversionWorker uses this protocol to remain engine-agnostic.
    """

    def convert(
        self, job: ConversionJob
    ) -> Generator[str, None, bool]:
        """Run conversion, yielding output lines.

        Args:
            job: The ConversionJob to convert.

        Yields:
            Lines from converter's output.

        Returns:
            True if conversion succeeded, False otherwise.
        """
        ...

    def get_process(self) -> Optional[subprocess.Popen[bytes]]:
        """Get the currently running subprocess, if any."""
        ...

    def is_available(self) -> bool:
        """Check if the converter binary exists and is usable."""
        ...


class FFmpegConverter:
    """Wraps FFmpeg subprocess for .ts -> .mp4 conversion.

    Two-pass conversion strategy:
      Pass 1: Stream copy (video + audio) with error tolerance.
              Fastest possible — no re-encoding.
      Pass 2: If pass 1 fails, re-encode audio to AAC while keeping
              video stream-copied. This handles corrupt ADTS frames
              that crash the aac_adtstoasc bitstream filter.

    Error tolerance flags (-err_detect, -fflags) are applied in both
    passes to skip corrupt MPEG-TS packets gracefully.
    """

    _UNSET = object()  # Sentinel for auto-resolution

    def __init__(self, ffmpeg_path: Optional[Path] | object = _UNSET) -> None:
        """Initialize with optional FFmpeg path.

        Args:
            ffmpeg_path: Path to ffmpeg.exe. If not provided, auto-resolves.
                        Pass None explicitly to indicate FFmpeg is unavailable.
        """
        if ffmpeg_path is FFmpegConverter._UNSET:
            self._ffmpeg_path = resolve_ffmpeg_path()
        else:
            self._ffmpeg_path = ffmpeg_path  # type: ignore[assignment]
        self._logger = get_logger()

    def build_command(self, job: ConversionJob, *, reencode_audio: bool = False) -> list[str]:
        """Build the FFmpeg command for a conversion job.

        Args:
            job: The ConversionJob with source and output paths.
            reencode_audio: If False (default), use -c copy for maximum speed.
                           If True, use -c:v copy -c:a aac to handle corrupt
                           AAC ADTS frames that fail the aac_adtstoasc filter.

        Returns:
            List of command arguments.

        Raises:
            FileNotFoundError: If FFmpeg binary is not available.
        """
        if self._ffmpeg_path is None:
            raise FileNotFoundError("FFmpeg binary not found")

        cmd = [
            str(self._ffmpeg_path),
            # Error tolerance flags (before -i, applied to input demuxer)
            "-err_detect", "ignore_err",
            "-fflags", "+genpts+discardcorrupt",
            # Input
            "-i", str(job.source_path),
            # Stream selection
            "-map", "0:v",
            "-map", "0:a",
        ]

        if reencode_audio:
            # Pass 2: video copy + audio re-encode
            cmd.extend([
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
            ])
        else:
            # Pass 1: full stream copy (fastest)
            cmd.extend(["-c", "copy"])

        cmd.extend([
            # Output format
            "-f", "mp4",
            "-movflags", "+faststart",
            "-max_muxing_queue_size", "1024",
            "-y",  # Overwrite output (conflict handled before reaching here)
            str(job.output_path),
        ])

        return cmd

    def convert(
        self, job: ConversionJob
    ) -> Generator[str, None, bool]:
        """Run FFmpeg conversion with automatic retry on corrupt streams.

        Two-pass strategy:
          Pass 1: Try -c copy (fast). If it succeeds, done.
          Pass 2: If pass 1 fails, retry with -c:a aac (re-encode audio).

        This is a generator that yields each line from FFmpeg's stderr output.
        The caller should parse these lines for progress information.

        Args:
            job: The ConversionJob to convert.

        Yields:
            Lines from FFmpeg stderr output.

        Returns:
            True if conversion succeeded (on either pass), False otherwise.

        Raises:
            FileNotFoundError: If FFmpeg binary is not available.
        """
        # === Pass 1: Fast stream copy ===
        success = yield from self._run_ffmpeg(job, reencode_audio=False)

        if success:
            return True

        # Pass 1 failed — check if output exists but might be corrupt/partial
        self._cleanup_output(job)

        # === Pass 2: Re-encode audio to handle corrupt AAC ===
        self._logger.info(
            f"Stream copy failed, retrying with audio re-encode: {job.source_path}"
        )
        success = yield from self._run_ffmpeg(job, reencode_audio=True)

        if success:
            self._logger.info(
                f"Retry succeeded with audio re-encode: {job.output_path}"
            )
        else:
            self._logger.error(
                f"Conversion failed even with audio re-encode: {job.source_path}"
            )

        return success

    def _run_ffmpeg(
        self, job: ConversionJob, *, reencode_audio: bool
    ) -> Generator[str, None, bool]:
        """Run a single FFmpeg pass, yielding stderr lines.

        Args:
            job: The ConversionJob to convert.
            reencode_audio: Whether to re-encode audio (pass 2) or copy (pass 1).

        Yields:
            Lines from FFmpeg stderr output.

        Returns:
            True if this pass succeeded, False otherwise.
        """
        cmd = self.build_command(job, reencode_audio=reencode_audio)
        mode = "audio re-encode" if reencode_audio else "stream copy"
        self._logger.info(
            f"Starting conversion ({mode}): {job.source_path} -> {job.output_path} "
            f"(size: {job.file_size} bytes)"
        )

        # Ensure output directory exists
        job.output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )

            # Store process reference for cancellation
            self._current_process = process

            # Read stderr line by line for progress
            if process.stderr:
                for raw_line in process.stderr:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if line:
                        yield line

            process.wait()

            success = process.returncode == 0
            if success:
                self._logger.info(f"Conversion completed ({mode}): {job.output_path}")
            else:
                self._logger.warning(
                    f"Conversion failed ({mode}, exit code {process.returncode}): "
                    f"{job.source_path}"
                )

            return success

        except FileNotFoundError:
            self._logger.error(f"FFmpeg not found: {self._ffmpeg_path}")
            raise
        except OSError as e:
            self._logger.error(f"OS error during conversion: {e}")
            return False
        finally:
            self._current_process = None

    def _cleanup_output(self, job: ConversionJob) -> None:
        """Remove partial/corrupt output file from a failed pass."""
        try:
            if job.output_path.exists():
                job.output_path.unlink()
                self._logger.info(f"Cleaned up failed output: {job.output_path}")
        except OSError as e:
            self._logger.warning(f"Failed to clean up output: {e}")

    def get_process(self) -> Optional[subprocess.Popen[bytes]]:
        """Get the currently running FFmpeg process, if any."""
        return getattr(self, "_current_process", None)

    def is_available(self) -> bool:
        """Check if the FFmpeg binary exists and is usable."""
        return self._ffmpeg_path is not None

"""QThread-based conversion worker for FFmpeg execution."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from src.core.converter import ConverterProtocol
from src.core.converter_factory import create_converter
from src.core.progress_parser import ProgressParser
from src.models.app_settings import AppSettings, ConverterEngine
from src.models.conversion_job import ConversionJob, ConversionStatus, QueueSummary
from src.utils.logger import get_logger


class ConversionWorker(QThread):
    """Worker thread for processing conversion jobs sequentially.

    Runs FFmpeg via subprocess on a background thread to keep the GUI responsive.
    Communicates progress and status via Qt signals.

    Signals:
        file_started(str): Emitted with job_id when a file starts converting.
        progress_updated(str, float): Emitted with (job_id, percentage).
        file_completed(str): Emitted with job_id on successful conversion.
        file_failed(str, str): Emitted with (job_id, error_message) on failure.
        file_skipped(str): Emitted with job_id when file is skipped.
        batch_completed(QueueSummary): Emitted when all files are processed.
        batch_cancelled(QueueSummary): Emitted when batch is cancelled.
    """

    file_started = Signal(str)
    progress_updated = Signal(str, float)
    file_completed = Signal(str)
    file_failed = Signal(str, str)
    file_skipped = Signal(str)
    batch_completed = Signal(object)  # QueueSummary
    batch_cancelled = Signal(object)  # QueueSummary

    def __init__(
        self,
        jobs: list[ConversionJob],
        settings: AppSettings,
        parent: object = None,
    ) -> None:
        super().__init__()
        self._jobs = jobs
        self._settings = settings
        self._cancelled = False
        self._converter: ConverterProtocol = create_converter(settings.converter_engine)
        self._progress_parser = ProgressParser()
        self._logger = get_logger()
        self._use_indeterminate = (
            settings.converter_engine == ConverterEngine.AVIDEMUX
        )

    def cancel(self) -> None:
        """Cancel the conversion process.

        Terminates the currently running FFmpeg subprocess and stops
        processing remaining files.
        """
        self._cancelled = True
        self._logger.info("Conversion cancelled by user")

        # Terminate currently running FFmpeg process
        process = self._converter.get_process()
        if process is not None:
            try:
                process.terminate()
            except OSError:
                pass

    def run(self) -> None:
        """Execute the conversion queue sequentially.

        Processes each job in order:
        1. Emit file_started signal
        2. Probe duration for progress tracking
        3. Run FFmpeg conversion
        4. Emit file_completed or file_failed
        5. Continue to next job (or stop on cancel)
        6. Emit batch_completed or batch_cancelled at end
        """
        completed = 0
        failed = 0
        skipped = 0
        cancelled = 0

        for job in self._jobs:
            if self._cancelled:
                # Mark remaining as still pending (not cancelled individually)
                cancelled = sum(
                    1 for j in self._jobs
                    if j.status == ConversionStatus.PENDING
                )
                break

            # Skip non-pending jobs
            if job.status != ConversionStatus.PENDING:
                continue

            # Start converting
            self.file_started.emit(job.id)
            job.set_status(ConversionStatus.CONVERTING)

            try:
                # Probe duration for progress tracking
                duration = self._progress_parser.probe_duration(job.source_path)
                job.duration = duration

                # Use indeterminate progress for Avidemux or fast/unknown duration
                if self._use_indeterminate or duration is None or duration < 2.0:
                    self.progress_updated.emit(job.id, -1.0)  # Indeterminate

                # Run conversion
                success = False
                stderr_gen = self._converter.convert(job)

                for line in stderr_gen:
                    if self._cancelled:
                        # Terminate and clean up
                        process = self._converter.get_process()
                        if process:
                            try:
                                process.terminate()
                            except OSError:
                                pass
                        # Clean up partial output
                        self._cleanup_partial_output(job)
                        job.set_status(ConversionStatus.CANCELLED)
                        cancelled += 1
                        break

                    # Parse progress (only for FFmpeg engine with known duration)
                    if not self._use_indeterminate and duration and duration >= 2.0:
                        percent = self._progress_parser.parse_progress(line, duration)
                        if percent is not None:
                            job.progress = percent
                            self.progress_updated.emit(job.id, percent)
                else:
                    # Generator exhausted normally — check return value
                    # The generator's return value indicates success
                    if job.output_path.exists() and job.output_path.stat().st_size > 0:
                        success = True

                if self._cancelled:
                    continue

                if success:
                    job.set_status(ConversionStatus.COMPLETE)
                    completed += 1
                    self.file_completed.emit(job.id)
                    self._logger.info(
                        f"Conversion complete: {job.source_path} "
                        f"(size: {job.file_size}, duration: {job.duration}s)"
                    )
                else:
                    error_msg = "Conversion failed"
                    job.set_status(ConversionStatus.ERROR, error=error_msg)
                    failed += 1
                    self.file_failed.emit(job.id, error_msg)
                    self._logger.error(f"Conversion failed: {job.source_path}")

            except FileNotFoundError as e:
                error_msg = str(e)
                job.set_status(ConversionStatus.ERROR, error=error_msg)
                failed += 1
                self.file_failed.emit(job.id, error_msg)
                self._logger.error(f"FFmpeg not found: {e}")
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                job.set_status(ConversionStatus.ERROR, error=error_msg)
                failed += 1
                self.file_failed.emit(job.id, error_msg)
                self._logger.error(f"Error converting {job.source_path}: {e}")

        # Build summary
        summary = QueueSummary(
            total=len(self._jobs),
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            skipped=skipped,
        )

        # Handle auto-delete source files if enabled
        if self._settings.auto_delete_source and not self._cancelled:
            self._auto_delete_sources()

        # Emit completion signal
        if self._cancelled:
            self.batch_cancelled.emit(summary)
        else:
            self.batch_completed.emit(summary)

        # Log session summary
        self._logger.info(
            f"Batch session complete: "
            f"total={summary.total}, completed={summary.completed}, "
            f"failed={summary.failed}, cancelled={summary.cancelled}, "
            f"skipped={summary.skipped}"
        )

    def _cleanup_partial_output(self, job: ConversionJob) -> None:
        """Delete partial output file if it exists."""
        try:
            if job.output_path.exists():
                job.output_path.unlink()
                self._logger.info(f"Cleaned up partial output: {job.output_path}")
        except OSError as e:
            self._logger.warning(f"Failed to clean up partial output: {e}")

    def _auto_delete_sources(self) -> None:
        """Delete source files for successfully completed jobs."""
        for job in self._jobs:
            if job.status == ConversionStatus.COMPLETE:
                try:
                    if job.source_path.exists():
                        job.source_path.unlink()
                        self._logger.info(f"Auto-deleted source file: {job.source_path}")
                except OSError as e:
                    self._logger.warning(f"Failed to auto-delete {job.source_path}: {e}")

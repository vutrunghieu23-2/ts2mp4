"""Conversion queue manager for batch operations."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.core.file_validator import FileValidator
from src.models.app_settings import AppSettings
from src.models.conversion_job import ConversionJob, ConversionStatus, QueueSummary
from src.utils.paths import resolve_output_path


class ConversionQueueManager:
    """Manages the ordered collection of conversion jobs.

    Provides methods to add, remove, and clear jobs. Enforces
    no-modification rules while the queue is running.
    """

    def __init__(self, settings: AppSettings) -> None:
        self._jobs: list[ConversionJob] = []
        self._settings = settings
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Whether a batch conversion is currently in progress."""
        return self._is_running

    @is_running.setter
    def is_running(self, value: bool) -> None:
        self._is_running = value

    @property
    def jobs(self) -> list[ConversionJob]:
        """Return the ordered list of jobs."""
        return list(self._jobs)

    def add(self, source_path: Path) -> ConversionJob:
        """Validate and add a new job to the queue.

        Args:
            source_path: Path to the source .ts file.

        Returns:
            The created ConversionJob.

        Raises:
            RuntimeError: If the queue is currently running.
            ValueError: If the file is invalid or a duplicate.
        """
        if self._is_running:
            raise RuntimeError("Cannot modify queue while conversion is running")

        if not FileValidator.validate_ts_file(source_path):
            raise ValueError(f"Invalid .ts file: {source_path}")

        existing_paths = [j.source_path for j in self._jobs]
        if FileValidator.is_duplicate(source_path, existing_paths):
            raise ValueError(f"Duplicate file: {source_path}")

        output_path = resolve_output_path(source_path, self._settings)
        job = ConversionJob.from_source(source_path, output_path)
        self._jobs.append(job)
        return job

    def remove(self, job_id: str) -> None:
        """Remove a pending job from the queue.

        Args:
            job_id: The job ID to remove.

        Raises:
            RuntimeError: If the queue is currently running.
            ValueError: If the job is not found.
        """
        if self._is_running:
            raise RuntimeError("Cannot modify queue while conversion is running")

        for i, job in enumerate(self._jobs):
            if job.id == job_id:
                self._jobs.pop(i)
                return

        raise ValueError(f"Job not found: {job_id}")

    def clear(self) -> None:
        """Remove all jobs from the queue.

        Raises:
            RuntimeError: If the queue is currently running.
        """
        if self._is_running:
            raise RuntimeError("Cannot modify queue while conversion is running")
        self._jobs.clear()

    def get_jobs(self) -> list[ConversionJob]:
        """Return all jobs in queue order."""
        return list(self._jobs)

    def get_pending_jobs(self) -> list[ConversionJob]:
        """Return all jobs with PENDING status."""
        return [j for j in self._jobs if j.status == ConversionStatus.PENDING]

    def get_summary(self) -> QueueSummary:
        """Return a summary of the current queue state.

        Returns:
            QueueSummary with counts by status.
        """
        return QueueSummary(
            total=len(self._jobs),
            completed=sum(1 for j in self._jobs if j.status == ConversionStatus.COMPLETE),
            failed=sum(1 for j in self._jobs if j.status == ConversionStatus.ERROR),
            cancelled=sum(1 for j in self._jobs if j.status == ConversionStatus.CANCELLED),
            skipped=sum(1 for j in self._jobs if j.status == ConversionStatus.SKIPPED),
            pending=sum(1 for j in self._jobs if j.status == ConversionStatus.PENDING),
        )

    def detect_conflicts(self) -> list[ConversionJob]:
        """Scan output paths for existing files.

        Returns:
            List of jobs whose output files already exist.
        """
        conflicts = []
        for job in self._jobs:
            if job.status == ConversionStatus.PENDING and job.output_path.exists():
                conflicts.append(job)
        return conflicts

    @property
    def total_count(self) -> int:
        return len(self._jobs)

    @property
    def completed_count(self) -> int:
        return sum(1 for j in self._jobs if j.status == ConversionStatus.COMPLETE)

    @property
    def failed_count(self) -> int:
        return sum(1 for j in self._jobs if j.status == ConversionStatus.ERROR)

    @property
    def pending_count(self) -> int:
        return sum(1 for j in self._jobs if j.status == ConversionStatus.PENDING)

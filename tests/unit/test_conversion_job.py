"""Unit tests for ConversionJob and ConversionStatus."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.models.conversion_job import (
    ConversionJob,
    ConversionStatus,
    QueueSummary,
    TERMINAL_STATUSES,
)


class TestConversionStatus:
    """Tests for the ConversionStatus enum."""

    def test_all_status_values_exist(self) -> None:
        """Verify all required status values are defined."""
        assert ConversionStatus.PENDING.value == "Pending"
        assert ConversionStatus.CONVERTING.value == "Converting"
        assert ConversionStatus.COMPLETE.value == "Complete"
        assert ConversionStatus.ERROR.value == "Error"
        assert ConversionStatus.CANCELLED.value == "Cancelled"
        assert ConversionStatus.SKIPPED.value == "Skipped"

    def test_terminal_statuses(self) -> None:
        """Verify terminal statuses are correct."""
        assert ConversionStatus.COMPLETE in TERMINAL_STATUSES
        assert ConversionStatus.ERROR in TERMINAL_STATUSES
        assert ConversionStatus.CANCELLED in TERMINAL_STATUSES
        assert ConversionStatus.SKIPPED in TERMINAL_STATUSES
        assert ConversionStatus.PENDING not in TERMINAL_STATUSES
        assert ConversionStatus.CONVERTING not in TERMINAL_STATUSES


class TestConversionJob:
    """Tests for the ConversionJob dataclass."""

    def test_creation_with_defaults(self, tmp_ts_file: Path) -> None:
        """Test job creation with minimal arguments."""
        job = ConversionJob(
            source_path=tmp_ts_file,
            output_path=tmp_ts_file.with_suffix(".mp4"),
        )
        assert job.source_path == tmp_ts_file
        assert job.output_path == tmp_ts_file.with_suffix(".mp4")
        assert job.status == ConversionStatus.PENDING
        assert job.progress == 0.0
        assert job.error_message is None
        assert job.file_size > 0  # Auto-populated from file
        assert isinstance(job.created_at, datetime)
        assert job.completed_at is None

    def test_uuid_uniqueness(self, tmp_ts_file: Path) -> None:
        """Test that each job gets a unique UUID."""
        job1 = ConversionJob(
            source_path=tmp_ts_file,
            output_path=tmp_ts_file.with_suffix(".mp4"),
        )
        job2 = ConversionJob(
            source_path=tmp_ts_file,
            output_path=tmp_ts_file.with_suffix(".mp4"),
        )
        assert job1.id != job2.id

    def test_from_source_factory(self, tmp_ts_file: Path) -> None:
        """Test the from_source factory method."""
        job = ConversionJob.from_source(tmp_ts_file)
        assert job.source_path == tmp_ts_file
        assert job.output_path == tmp_ts_file.with_suffix(".mp4")
        assert job.status == ConversionStatus.PENDING

    def test_from_source_with_custom_output(self, tmp_ts_file: Path, tmp_path: Path) -> None:
        """Test from_source with custom output path."""
        custom_output = tmp_path / "custom_output.mp4"
        job = ConversionJob.from_source(tmp_ts_file, output_path=custom_output)
        assert job.output_path == custom_output

    def test_filename_property(self, tmp_ts_file: Path) -> None:
        """Test the filename property returns the base name."""
        job = ConversionJob.from_source(tmp_ts_file)
        assert job.filename == tmp_ts_file.name

    def test_source_directory_property(self, tmp_ts_file: Path) -> None:
        """Test the source_directory property."""
        job = ConversionJob.from_source(tmp_ts_file)
        assert job.source_directory == str(tmp_ts_file.parent)


class TestStatusTransitions:
    """Tests for valid and invalid status transitions."""

    def test_pending_to_converting(self, tmp_ts_file: Path) -> None:
        """Test valid PENDING -> CONVERTING transition."""
        job = ConversionJob.from_source(tmp_ts_file)
        job.set_status(ConversionStatus.CONVERTING)
        assert job.status == ConversionStatus.CONVERTING

    def test_pending_to_skipped(self, tmp_ts_file: Path) -> None:
        """Test valid PENDING -> SKIPPED transition."""
        job = ConversionJob.from_source(tmp_ts_file)
        job.set_status(ConversionStatus.SKIPPED)
        assert job.status == ConversionStatus.SKIPPED
        assert job.completed_at is not None

    def test_converting_to_complete(self, tmp_ts_file: Path) -> None:
        """Test valid CONVERTING -> COMPLETE transition."""
        job = ConversionJob.from_source(tmp_ts_file)
        job.set_status(ConversionStatus.CONVERTING)
        job.set_status(ConversionStatus.COMPLETE)
        assert job.status == ConversionStatus.COMPLETE
        assert job.progress == 100.0
        assert job.completed_at is not None

    def test_converting_to_error(self, tmp_ts_file: Path) -> None:
        """Test valid CONVERTING -> ERROR transition with message."""
        job = ConversionJob.from_source(tmp_ts_file)
        job.set_status(ConversionStatus.CONVERTING)
        job.set_status(ConversionStatus.ERROR, error="FFmpeg failed")
        assert job.status == ConversionStatus.ERROR
        assert job.error_message == "FFmpeg failed"
        assert job.completed_at is not None

    def test_converting_to_cancelled(self, tmp_ts_file: Path) -> None:
        """Test valid CONVERTING -> CANCELLED transition."""
        job = ConversionJob.from_source(tmp_ts_file)
        job.set_status(ConversionStatus.CONVERTING)
        job.set_status(ConversionStatus.CANCELLED)
        assert job.status == ConversionStatus.CANCELLED
        assert job.completed_at is not None

    def test_invalid_pending_to_complete(self, tmp_ts_file: Path) -> None:
        """Test invalid PENDING -> COMPLETE transition raises ValueError."""
        job = ConversionJob.from_source(tmp_ts_file)
        with pytest.raises(ValueError, match="Invalid status transition"):
            job.set_status(ConversionStatus.COMPLETE)

    def test_invalid_complete_to_converting(self, tmp_ts_file: Path) -> None:
        """Test that terminal states cannot transition."""
        job = ConversionJob.from_source(tmp_ts_file)
        job.set_status(ConversionStatus.CONVERTING)
        job.set_status(ConversionStatus.COMPLETE)
        with pytest.raises(ValueError, match="Invalid status transition"):
            job.set_status(ConversionStatus.CONVERTING)

    def test_is_terminal_property(self, tmp_ts_file: Path) -> None:
        """Test is_terminal property for various states."""
        job = ConversionJob.from_source(tmp_ts_file)
        assert not job.is_terminal
        job.set_status(ConversionStatus.CONVERTING)
        assert not job.is_terminal
        job.set_status(ConversionStatus.COMPLETE)
        assert job.is_terminal


class TestQueueSummary:
    """Tests for QueueSummary."""

    def test_default_values(self) -> None:
        """Test QueueSummary default values are all zero."""
        summary = QueueSummary()
        assert summary.total == 0
        assert summary.completed == 0
        assert summary.failed == 0
        assert summary.cancelled == 0
        assert summary.skipped == 0

    def test_custom_values(self) -> None:
        """Test QueueSummary with custom values."""
        summary = QueueSummary(total=10, completed=7, failed=2, skipped=1)
        assert summary.total == 10
        assert summary.completed == 7
        assert summary.failed == 2
        assert summary.cancelled == 0
        assert summary.skipped == 1

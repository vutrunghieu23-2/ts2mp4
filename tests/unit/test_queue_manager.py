"""Unit tests for ConversionQueueManager."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.queue_manager import ConversionQueueManager
from src.models.app_settings import AppSettings
from src.models.conversion_job import ConversionStatus


class TestQueueManagerAdd:
    """Tests for adding files to the queue."""

    def test_add_valid_file(self, tmp_ts_file: Path) -> None:
        """Test adding a valid .ts file."""
        manager = ConversionQueueManager(AppSettings())
        job = manager.add(tmp_ts_file)
        assert job.source_path == tmp_ts_file
        assert job.status == ConversionStatus.PENDING
        assert manager.total_count == 1

    def test_add_duplicate_raises(self, tmp_ts_file: Path) -> None:
        """Test that adding a duplicate raises ValueError."""
        manager = ConversionQueueManager(AppSettings())
        manager.add(tmp_ts_file)
        with pytest.raises(ValueError, match="Duplicate file"):
            manager.add(tmp_ts_file)

    def test_add_invalid_file_raises(self, tmp_non_ts_file: Path) -> None:
        """Test that adding a non-.ts file raises ValueError."""
        manager = ConversionQueueManager(AppSettings())
        with pytest.raises(ValueError, match="Invalid .ts file"):
            manager.add(tmp_non_ts_file)

    def test_add_while_running_raises(self, tmp_ts_file: Path) -> None:
        """Test that adding while running raises RuntimeError."""
        manager = ConversionQueueManager(AppSettings())
        manager.is_running = True
        with pytest.raises(RuntimeError, match="Cannot modify queue"):
            manager.add(tmp_ts_file)


class TestQueueManagerRemove:
    """Tests for removing files from the queue."""

    def test_remove_existing_job(self, tmp_ts_file: Path) -> None:
        """Test removing an existing job."""
        manager = ConversionQueueManager(AppSettings())
        job = manager.add(tmp_ts_file)
        manager.remove(job.id)
        assert manager.total_count == 0

    def test_remove_nonexistent_raises(self) -> None:
        """Test removing a nonexistent job raises ValueError."""
        manager = ConversionQueueManager(AppSettings())
        with pytest.raises(ValueError, match="Job not found"):
            manager.remove("nonexistent-id")

    def test_remove_while_running_raises(self, tmp_ts_file: Path) -> None:
        """Test that removing while running raises RuntimeError."""
        manager = ConversionQueueManager(AppSettings())
        job = manager.add(tmp_ts_file)
        manager.is_running = True
        with pytest.raises(RuntimeError, match="Cannot modify queue"):
            manager.remove(job.id)


class TestQueueManagerClear:
    """Tests for clearing the queue."""

    def test_clear_all(self, tmp_ts_files: list[Path]) -> None:
        """Test clearing all jobs."""
        manager = ConversionQueueManager(AppSettings())
        for f in tmp_ts_files:
            manager.add(f)
        assert manager.total_count == len(tmp_ts_files)
        manager.clear()
        assert manager.total_count == 0

    def test_clear_while_running_raises(self, tmp_ts_file: Path) -> None:
        """Test that clearing while running raises RuntimeError."""
        manager = ConversionQueueManager(AppSettings())
        manager.add(tmp_ts_file)
        manager.is_running = True
        with pytest.raises(RuntimeError, match="Cannot modify queue"):
            manager.clear()


class TestQueueManagerProcessing:
    """Tests for queue processing logic."""

    def test_sequential_order(self, tmp_ts_files: list[Path]) -> None:
        """Test that jobs maintain sequential order."""
        manager = ConversionQueueManager(AppSettings())
        for f in tmp_ts_files:
            manager.add(f)

        jobs = manager.get_jobs()
        for i, (job, file) in enumerate(zip(jobs, tmp_ts_files)):
            assert job.source_path == file

    def test_get_pending_jobs(self, tmp_ts_files: list[Path]) -> None:
        """Test getting only pending jobs."""
        manager = ConversionQueueManager(AppSettings())
        for f in tmp_ts_files:
            manager.add(f)

        # Mark some as complete
        jobs = manager.get_jobs()
        jobs[0].set_status(ConversionStatus.CONVERTING)
        jobs[0].set_status(ConversionStatus.COMPLETE)

        pending = manager.get_pending_jobs()
        assert len(pending) == len(tmp_ts_files) - 1

    def test_summary(self, tmp_ts_files: list[Path]) -> None:
        """Test queue summary generation."""
        manager = ConversionQueueManager(AppSettings())
        for f in tmp_ts_files:
            manager.add(f)

        # Set various statuses
        jobs = manager.get_jobs()
        jobs[0].set_status(ConversionStatus.CONVERTING)
        jobs[0].set_status(ConversionStatus.COMPLETE)
        jobs[1].set_status(ConversionStatus.CONVERTING)
        jobs[1].set_status(ConversionStatus.ERROR, error="test error")

        summary = manager.get_summary()
        assert summary.total == len(tmp_ts_files)
        assert summary.completed == 1
        assert summary.failed == 1
        assert summary.pending == len(tmp_ts_files) - 2  # Remaining still in the count

    def test_error_and_continue(self, tmp_ts_files: list[Path]) -> None:
        """Test that one error doesn't prevent others from being pending."""
        manager = ConversionQueueManager(AppSettings())
        for f in tmp_ts_files:
            manager.add(f)

        jobs = manager.get_jobs()
        # First job fails
        jobs[0].set_status(ConversionStatus.CONVERTING)
        jobs[0].set_status(ConversionStatus.ERROR, error="fail")

        # Remaining are still pending
        pending = manager.get_pending_jobs()
        assert len(pending) == len(tmp_ts_files) - 1

    def test_detect_conflicts(self, tmp_path: Path) -> None:
        """Test conflict detection for existing output files."""
        # Create .ts files and their would-be .mp4 outputs
        ts_file = tmp_path / "existing.ts"
        ts_file.write_bytes(b"\x47" * 188)
        mp4_file = tmp_path / "existing.mp4"
        mp4_file.write_bytes(b"\x00" * 100)  # Existing output

        manager = ConversionQueueManager(AppSettings())
        manager.add(ts_file)

        conflicts = manager.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].source_path == ts_file

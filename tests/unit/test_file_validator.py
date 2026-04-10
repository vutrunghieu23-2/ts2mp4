"""Unit tests for FileValidator."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.file_validator import FileValidator


class TestValidateTsFile:
    """Tests for the validate_ts_file method."""

    def test_valid_ts_file(self, tmp_ts_file: Path) -> None:
        """Test that a valid .ts file passes validation."""
        assert FileValidator.validate_ts_file(tmp_ts_file) is True

    def test_non_ts_extension_rejected(self, tmp_non_ts_file: Path) -> None:
        """Test that non-.ts files are rejected."""
        assert FileValidator.validate_ts_file(tmp_non_ts_file) is False

    def test_nonexistent_file_rejected(self, tmp_path: Path) -> None:
        """Test that nonexistent files are rejected."""
        fake_path = tmp_path / "nonexistent.ts"
        assert FileValidator.validate_ts_file(fake_path) is False

    def test_directory_rejected(self, tmp_path: Path) -> None:
        """Test that directories are rejected even with .ts in name."""
        ts_dir = tmp_path / "folder.ts"
        ts_dir.mkdir()
        assert FileValidator.validate_ts_file(ts_dir) is False

    def test_uppercase_extension(self, tmp_path: Path) -> None:
        """Test that .TS (uppercase) extension is accepted."""
        ts_file = tmp_path / "video.TS"
        ts_file.write_bytes(b"\x47" * 188)
        assert FileValidator.validate_ts_file(ts_file) is True

    def test_string_path_accepted(self, tmp_ts_file: Path) -> None:
        """Test that string paths are accepted."""
        assert FileValidator.validate_ts_file(str(tmp_ts_file)) is True

    def test_mp4_extension_rejected(self, tmp_path: Path) -> None:
        """Test that .mp4 files are rejected."""
        mp4_file = tmp_path / "video.mp4"
        mp4_file.write_bytes(b"\x00" * 100)
        assert FileValidator.validate_ts_file(mp4_file) is False


class TestFilterValidFiles:
    """Tests for the filter_valid_files method."""

    def test_all_valid(self, tmp_ts_files: list[Path]) -> None:
        """Test filtering when all files are valid .ts files."""
        valid, rejected = FileValidator.filter_valid_files(tmp_ts_files)
        assert len(valid) == len(tmp_ts_files)
        assert len(rejected) == 0

    def test_all_rejected(self, tmp_path: Path) -> None:
        """Test filtering when no files are valid."""
        files = [
            tmp_path / "doc.txt",
            tmp_path / "img.png",
        ]
        for f in files:
            f.write_bytes(b"\x00" * 10)
        valid, rejected = FileValidator.filter_valid_files(files)
        assert len(valid) == 0
        assert len(rejected) == len(files)

    def test_mixed_files(self, tmp_ts_file: Path, tmp_non_ts_file: Path) -> None:
        """Test filtering with a mix of valid and invalid files."""
        valid, rejected = FileValidator.filter_valid_files([tmp_ts_file, tmp_non_ts_file])
        assert len(valid) == 1
        assert len(rejected) == 1
        assert valid[0] == tmp_ts_file
        assert rejected[0] == tmp_non_ts_file

    def test_empty_list(self) -> None:
        """Test filtering an empty list."""
        valid, rejected = FileValidator.filter_valid_files([])
        assert len(valid) == 0
        assert len(rejected) == 0


class TestIsDuplicate:
    """Tests for the is_duplicate method."""

    def test_duplicate_detected(self, tmp_ts_file: Path) -> None:
        """Test that a duplicate is correctly detected."""
        existing = [tmp_ts_file]
        assert FileValidator.is_duplicate(tmp_ts_file, existing) is True

    def test_no_duplicate(self, tmp_ts_file: Path, tmp_path: Path) -> None:
        """Test that a non-duplicate is correctly identified."""
        other_file = tmp_path / "other.ts"
        other_file.write_bytes(b"\x47" * 188)
        assert FileValidator.is_duplicate(other_file, [tmp_ts_file]) is False

    def test_string_vs_path_comparison(self, tmp_ts_file: Path) -> None:
        """Test that string and Path comparisons work for duplicate detection."""
        existing = [tmp_ts_file]
        assert FileValidator.is_duplicate(str(tmp_ts_file), existing) is True

    def test_empty_existing(self, tmp_ts_file: Path) -> None:
        """Test no duplicate in empty collection."""
        assert FileValidator.is_duplicate(tmp_ts_file, []) is False

    def test_set_existing(self, tmp_ts_file: Path) -> None:
        """Test duplicate detection with set collection."""
        existing = {tmp_ts_file}
        assert FileValidator.is_duplicate(tmp_ts_file, existing) is True

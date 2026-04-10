"""File validation utilities for .ts files."""
from __future__ import annotations

from pathlib import Path


class FileValidator:
    """Validates .ts files for import into the conversion queue.

    Provides methods to check file extensions, existence, and detect
    duplicates in the current queue.
    """

    TS_EXTENSION = ".ts"

    @staticmethod
    def validate_ts_file(path: Path | str) -> bool:
        """Check if a path is a valid .ts file.

        A valid .ts file must:
        - Have the .ts extension (case-insensitive)
        - Exist on disk
        - Be a file (not a directory)

        Args:
            path: Path to validate.

        Returns:
            True if the path is a valid .ts file, False otherwise.
        """
        p = Path(path)
        return p.exists() and p.is_file() and p.suffix.lower() == FileValidator.TS_EXTENSION

    @staticmethod
    def filter_valid_files(paths: list[Path | str]) -> tuple[list[Path], list[Path]]:
        """Separate paths into valid .ts files and rejected files.

        Args:
            paths: List of file paths to filter.

        Returns:
            A tuple of (valid_paths, rejected_paths).
        """
        valid: list[Path] = []
        rejected: list[Path] = []

        for path in paths:
            p = Path(path)
            if FileValidator.validate_ts_file(p):
                valid.append(p)
            else:
                rejected.append(p)

        return valid, rejected

    @staticmethod
    def is_duplicate(path: Path | str, existing_paths: list[Path] | set[Path]) -> bool:
        """Check if a path already exists in the given collection.

        Comparison is done using resolved absolute paths to avoid
        duplicates caused by relative paths or symlinks.

        Args:
            path: Path to check.
            existing_paths: Collection of already-queued paths.

        Returns:
            True if the path is a duplicate, False otherwise.
        """
        check_path = Path(path).resolve()
        resolved_existing = {Path(p).resolve() for p in existing_paths}
        return check_path in resolved_existing

"""Progress display widget for the file list table."""
from __future__ import annotations

from PySide6.QtWidgets import QProgressBar, QWidget


class ProgressWidget(QProgressBar):
    """Per-file progress bar widget for the FileListWidget table.

    Shows:
    - Percentage-based progress for large files (> 100MB)
    - Indeterminate spinning indicator for small files (< 100MB)
    """

    LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(True)

    def set_indeterminate(self) -> None:
        """Switch to indeterminate (spinning) mode."""
        self.setRange(0, 0)

    def set_progress(self, percent: float) -> None:
        """Set progress percentage.

        Args:
            percent: Progress percentage (0.0 - 100.0).
                    Negative values trigger indeterminate mode.
        """
        if percent < 0:
            self.set_indeterminate()
        else:
            self.setRange(0, 100)
            self.setValue(int(min(100.0, percent)))

"""File list widget (QTableWidget) for displaying the conversion queue."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMenu,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from src.models.conversion_job import ConversionJob, ConversionStatus


# Status display mapping
_STATUS_DISPLAY = {
    ConversionStatus.PENDING: ("⏸ Pending", QColor(180, 180, 180)),
    ConversionStatus.CONVERTING: ("⏳ Converting", QColor(70, 130, 180)),
    ConversionStatus.COMPLETE: ("✅ Complete", QColor(76, 175, 80)),
    ConversionStatus.ERROR: ("❌ Error", QColor(244, 67, 54)),
    ConversionStatus.CANCELLED: ("🚫 Cancelled", QColor(255, 152, 0)),
    ConversionStatus.SKIPPED: ("⏭️ Skipped", QColor(158, 158, 158)),
}


class FileListWidget(QTableWidget):
    """Table widget displaying the conversion file queue.

    Columns: #, File Name, Source Path, Status, Progress

    Signals:
        file_double_clicked(str): Emitted with job_id on row double-click.
        context_menu_preview(str): Emitted with job_id for preview action.
        context_menu_remove(str): Emitted with job_id for remove action.
        context_menu_open_folder(str): Emitted with job_id for open folder action.
    """

    file_double_clicked = Signal(str)
    context_menu_preview = Signal(str)
    context_menu_remove = Signal(str)
    context_menu_open_folder = Signal(str)
    files_dropped = Signal(list)

    COLUMNS = ["#", "File Name", "Source Path", "Status", "Progress"]
    COL_INDEX = 0
    COL_FILENAME = 1
    COL_SOURCE_PATH = 2
    COL_STATUS = 3
    COL_PROGRESS = 4

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._jobs: dict[str, ConversionJob] = {}
        self._job_row_map: dict[str, int] = {}
        self._is_running = False

        self.setAcceptDrops(True)
        self._setup_table()

    def _setup_table(self) -> None:
        """Configure table appearance and behavior."""
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)

        # Configure header
        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_INDEX, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_FILENAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_SOURCE_PATH, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_PROGRESS, QHeaderView.ResizeMode.Fixed)

        self.setColumnWidth(self.COL_INDEX, 40)
        self.setColumnWidth(self.COL_STATUS, 120)
        self.setColumnWidth(self.COL_PROGRESS, 150)

        # Selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Double-click
        self.doubleClicked.connect(self._on_double_click)

    # ========== Drag & Drop ==========

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drag events with file URLs or text."""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Continue accepting drag events during move."""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file drop - emit paths as signal."""
        from src.ui.drop_zone import extract_file_paths_from_drop

        paths = extract_file_paths_from_drop(event)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def set_running(self, running: bool) -> None:
        """Set whether the queue is currently running conversion."""
        self._is_running = running

    def add_job(self, job: ConversionJob) -> None:
        """Add a conversion job as a new row in the table.

        Args:
            job: The ConversionJob to add.
        """
        row = self.rowCount()
        self.insertRow(row)

        self._jobs[job.id] = job
        self._job_row_map[job.id] = row

        # # column
        index_item = QTableWidgetItem(str(row + 1))
        index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, self.COL_INDEX, index_item)

        # File Name
        self.setItem(row, self.COL_FILENAME, QTableWidgetItem(job.filename))

        # Source Path
        self.setItem(row, self.COL_SOURCE_PATH, QTableWidgetItem(job.source_directory))

        # Status
        status_text, status_color = _STATUS_DISPLAY.get(
            job.status, ("Unknown", QColor(128, 128, 128))
        )
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(status_color)
        self.setItem(row, self.COL_STATUS, status_item)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setVisible(False)  # Hidden until converting
        self.setCellWidget(row, self.COL_PROGRESS, progress_bar)

    def update_job_status(self, job_id: str, status: ConversionStatus, error: str = "") -> None:
        """Update the status display for a job.

        Args:
            job_id: The job ID to update.
            status: The new status.
            error: Optional error message for tooltip.
        """
        if job_id not in self._job_row_map:
            return

        row = self._job_row_map[job_id]
        status_text, status_color = _STATUS_DISPLAY.get(status, ("Unknown", QColor(128, 128, 128)))

        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(status_color)
        if error:
            status_item.setToolTip(f"Error: {error}")
        self.setItem(row, self.COL_STATUS, status_item)

        # Show/hide progress bar
        progress_bar = self.cellWidget(row, self.COL_PROGRESS)
        if isinstance(progress_bar, QProgressBar):
            progress_bar.setVisible(status == ConversionStatus.CONVERTING)

    def update_job_progress(self, job_id: str, percent: float) -> None:
        """Update the progress bar for a job.

        Args:
            job_id: The job ID to update.
            percent: Progress percentage (0.0 - 100.0).
        """
        if job_id not in self._job_row_map:
            return

        row = self._job_row_map[job_id]
        progress_bar = self.cellWidget(row, self.COL_PROGRESS)
        if isinstance(progress_bar, QProgressBar):
            progress_bar.setVisible(True)
            if percent < 0:
                # Indeterminate mode
                progress_bar.setRange(0, 0)
            else:
                progress_bar.setRange(0, 100)
                progress_bar.setValue(int(percent))

    def remove_selected(self) -> list[str]:
        """Remove selected rows from the table.

        Returns:
            List of removed job IDs.
        """
        removed_ids: list[str] = []
        selected_rows = sorted(set(idx.row() for idx in self.selectedIndexes()), reverse=True)

        for row in selected_rows:
            job_id = self._get_job_id_at_row(row)
            if job_id:
                removed_ids.append(job_id)
                del self._jobs[job_id]
                del self._job_row_map[job_id]
            self.removeRow(row)

        # Rebuild row map after removal
        self._rebuild_row_map()
        return removed_ids

    def clear_all(self) -> list[str]:
        """Remove all rows from the table.

        Returns:
            List of all removed job IDs.
        """
        removed_ids = list(self._jobs.keys())
        self._jobs.clear()
        self._job_row_map.clear()
        self.setRowCount(0)
        return removed_ids

    def get_all_jobs(self) -> list[ConversionJob]:
        """Return all jobs in queue order."""
        jobs_by_row = sorted(self._job_row_map.items(), key=lambda x: x[1])
        return [self._jobs[job_id] for job_id, _ in jobs_by_row]

    def get_all_source_paths(self) -> set[Path]:
        """Return all source paths currently in the queue."""
        return {job.source_path for job in self._jobs.values()}

    def get_job_count(self) -> int:
        """Return the number of jobs in the queue."""
        return len(self._jobs)

    def get_pending_count(self) -> int:
        """Return the number of pending jobs."""
        return sum(1 for j in self._jobs.values() if j.status == ConversionStatus.PENDING)

    def _get_job_id_at_row(self, row: int) -> Optional[str]:
        """Find the job ID for a given row index."""
        for job_id, job_row in self._job_row_map.items():
            if job_row == row:
                return job_id
        return None

    def _rebuild_row_map(self) -> None:
        """Rebuild the job_id -> row mapping after row operations."""
        new_map: dict[str, int] = {}
        for row in range(self.rowCount()):
            for job_id, old_row in self._job_row_map.items():
                if job_id in new_map:
                    continue
            # Reassign by matching filename
            filename_item = self.item(row, self.COL_FILENAME)
            if filename_item:
                for job_id, job in self._jobs.items():
                    if job.filename == filename_item.text() and job_id not in new_map:
                        new_map[job_id] = row
                        break

            # Update index column
            index_item = self.item(row, self.COL_INDEX)
            if index_item:
                index_item.setText(str(row + 1))

        self._job_row_map = new_map

    def _show_context_menu(self, pos: object) -> None:
        """Show right-click context menu."""
        from PySide6.QtCore import QPoint

        if not isinstance(pos, QPoint):
            return

        item = self.itemAt(pos)
        if item is None:
            return

        row = item.row()
        job_id = self._get_job_id_at_row(row)
        if job_id is None:
            return

        menu = QMenu(self)

        # Preview action
        preview_action = QAction("Preview", self)
        preview_action.triggered.connect(lambda: self.context_menu_preview.emit(job_id))
        menu.addAction(preview_action)

        # Remove action (only when not running)
        if not self._is_running:
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(lambda: self.context_menu_remove.emit(job_id))
            menu.addAction(remove_action)

        menu.addSeparator()

        # Open containing folder
        open_folder_action = QAction("Open Containing Folder", self)
        open_folder_action.triggered.connect(
            lambda: self.context_menu_open_folder.emit(job_id)
        )
        menu.addAction(open_folder_action)

        menu.exec(self.mapToGlobal(pos))

    def _on_double_click(self, index: object) -> None:
        """Handle double-click on a row."""
        from PySide6.QtCore import QModelIndex

        if not isinstance(index, QModelIndex):
            return

        row = index.row()
        job_id = self._get_job_id_at_row(row)
        if job_id:
            self.file_double_clicked.emit(job_id)

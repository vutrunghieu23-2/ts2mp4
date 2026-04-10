"""Main application window with toolbar, file queue, and action buttons."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.file_validator import FileValidator
from src.models.app_settings import AppSettings
from src.models.conversion_job import ConversionJob, ConversionStatus, QueueSummary
from src.ui.drop_zone import DropZone
from src.ui.file_list_widget import FileListWidget
from src.utils.logger import get_logger
from src.utils.paths import resolve_output_path


class MainWindow(QMainWindow):
    """Main application window for Ts2Mp4 Video Container Converter.

    Layout per ui-contracts.md:
    - Toolbar: Add Files, Remove, Clear All, Settings
    - Output Directory bar
    - File Queue (DropZone + FileListWidget)
    - Action buttons: Start Conversion, Cancel
    - Status bar
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = AppSettings.load()
        self._ffmpeg_available = False
        self._is_running = False
        self._worker: object | None = None  # Will be ConversionWorker when needed
        self._logger = get_logger()

        self._setup_ui()
        self._connect_signals()
        self._restore_geometry()
        self._update_ui_state()

    def _setup_ui(self) -> None:
        """Create and lay out all UI components."""
        self.setWindowTitle("Ts2Mp4 — Video Container Converter")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # === Toolbar ===
        self._create_toolbar()

        # === Output Directory Bar ===
        output_bar = QHBoxLayout()
        output_label = QLabel("📁 Output:")
        self._output_path_label = QLabel(self._get_output_display_text())
        self._output_path_label.setStyleSheet("color: #666; font-style: italic;")
        self._btn_browse = QPushButton("Browse...")
        self._btn_browse.setObjectName("btn_browse")
        self._btn_browse.setFixedWidth(100)
        output_bar.addWidget(output_label)
        output_bar.addWidget(self._output_path_label, 1)
        output_bar.addWidget(self._btn_browse)
        layout.addLayout(output_bar)

        # === File Queue Area ===
        self._drop_zone = DropZone()
        self._file_list = FileListWidget()

        # Stack: show drop zone placeholder when empty, file list when populated
        layout.addWidget(self._file_list, 1)
        layout.addWidget(self._drop_zone)

        # === Action Buttons ===
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        self._btn_start = QPushButton("▶️ Start Conversion")
        self._btn_start.setObjectName("btn_start")
        self._btn_start.setMinimumWidth(180)
        self._btn_start.setMinimumHeight(40)
        self._btn_start.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; "
            "font-weight: bold; border-radius: 6px; padding: 8px 20px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666; }"
        )

        self._btn_cancel = QPushButton("❌ Cancel")
        self._btn_cancel.setObjectName("btn_cancel")
        self._btn_cancel.setMinimumWidth(120)
        self._btn_cancel.setMinimumHeight(40)
        self._btn_cancel.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; font-size: 14px; "
            "font-weight: bold; border-radius: 6px; padding: 8px 20px; }"
            "QPushButton:hover { background-color: #da190b; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666; }"
        )

        action_bar.addWidget(self._btn_start)
        action_bar.addWidget(self._btn_cancel)
        action_bar.addStretch()
        layout.addLayout(action_bar)

        # === Status Bar ===
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _create_toolbar(self) -> None:
        """Create the toolbar with Add Files, Remove, Clear All, Settings."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Add Files
        self._action_add_files = QAction("📂 Add Files", self)
        self._action_add_files.setObjectName("btn_add_files")
        toolbar.addAction(self._action_add_files)

        # Remove
        self._action_remove = QAction("🗑️ Remove", self)
        self._action_remove.setObjectName("btn_remove")
        toolbar.addAction(self._action_remove)

        # Clear All
        self._action_clear_all = QAction("🧹 Clear All", self)
        self._action_clear_all.setObjectName("btn_clear_all")
        toolbar.addAction(self._action_clear_all)

        toolbar.addSeparator()

        # Settings
        self._action_settings = QAction("⚙️ Settings", self)
        self._action_settings.setObjectName("btn_settings")
        toolbar.addAction(self._action_settings)

    def _connect_signals(self) -> None:
        """Wire up all signal/slot connections."""
        # Toolbar actions
        self._action_add_files.triggered.connect(self._on_add_files)
        self._action_remove.triggered.connect(self._on_remove)
        self._action_clear_all.triggered.connect(self._on_clear_all)
        self._action_settings.triggered.connect(self._on_settings)

        # Action buttons
        self._btn_start.clicked.connect(self._on_start_conversion)
        self._btn_cancel.clicked.connect(self._on_cancel)
        self._btn_browse.clicked.connect(self._on_browse_output)

        # Drop zone
        self._drop_zone.files_dropped.connect(self._on_files_dropped)

        # File list drag & drop
        self._file_list.files_dropped.connect(self._on_files_dropped)

        # File list context menu
        self._file_list.file_double_clicked.connect(self._on_file_preview)
        self._file_list.context_menu_preview.connect(self._on_file_preview)
        self._file_list.context_menu_remove.connect(self._on_context_remove)
        self._file_list.context_menu_open_folder.connect(self._on_open_containing_folder)

    def set_ffmpeg_available(self, available: bool) -> None:
        """Set whether FFmpeg is available on this system."""
        self._ffmpeg_available = available
        self._update_ui_state()

    # ========== Event Handlers ==========

    def _on_files_dropped(self, paths: list[str]) -> None:
        """Handle files dropped onto the drop zone."""
        self._import_files([Path(p) for p in paths])

    def _on_add_files(self) -> None:
        """Handle Add Files toolbar action - open file dialog."""
        start_dir = ""
        if self._settings.last_import_directory:
            start_dir = self._settings.last_import_directory

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select .ts Video Files",
            start_dir,
            "TS Video Files (*.ts);;All Files (*)",
        )

        if file_paths:
            # Update last import directory
            first_dir = str(Path(file_paths[0]).parent)
            self._settings.last_import_directory = first_dir
            self._settings.save()

            self._import_files([Path(p) for p in file_paths])

    def _on_remove(self) -> None:
        """Handle Remove toolbar action."""
        removed = self._file_list.remove_selected()
        if removed:
            self._show_status_message(f"Removed {len(removed)} file(s)")
        self._update_ui_state()

    def _on_clear_all(self) -> None:
        """Handle Clear All toolbar action."""
        count = self._file_list.get_job_count()
        if count > 0:
            removed = self._file_list.clear_all()
            self._show_status_message(f"Cleared {len(removed)} file(s)")
        self._update_ui_state()

    def _on_settings(self) -> None:
        """Handle Settings toolbar action."""
        # Settings dialog will be implemented in Phase 11
        from src.ui.dialogs import SettingsDialog

        dialog = SettingsDialog(self._settings, self)
        if dialog.exec():
            self._settings = dialog.get_settings()
            self._settings.save()
            self._output_path_label.setText(self._get_output_display_text())

    def _on_start_conversion(self) -> None:
        """Handle Start Conversion button click."""
        if not self._ffmpeg_available:
            QMessageBox.critical(
                self,
                "FFmpeg Not Available",
                "FFmpeg is required for conversion but was not found.\n"
                "Please install FFmpeg and restart the application.",
            )
            return

        jobs = self._file_list.get_all_jobs()
        pending_jobs = [j for j in jobs if j.status == ConversionStatus.PENDING]

        if not pending_jobs:
            self._show_status_message("No files to convert")
            return

        self._start_batch_conversion(pending_jobs)

    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        if self._worker is not None and hasattr(self._worker, "cancel"):
            self._worker.cancel()  # type: ignore[union-attr]

    def _on_browse_output(self) -> None:
        """Handle Browse button for output directory."""
        current_dir = self._settings.output_directory or ""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir,
        )
        if dir_path:
            self._settings.output_directory = dir_path
            self._settings.save()
            self._output_path_label.setText(self._get_output_display_text())

    def _on_file_preview(self, job_id: str) -> None:
        """Open a file in the default system media player."""
        jobs = self._file_list.get_all_jobs()
        for job in jobs:
            if job.id == job_id:
                try:
                    os.startfile(str(job.source_path))  # type: ignore[attr-defined]
                except OSError as e:
                    self._logger.error(f"Failed to preview file: {e}")
                break

    def _on_context_remove(self, job_id: str) -> None:
        """Handle context menu Remove action."""
        # Select the row first, then remove
        for row in range(self._file_list.rowCount()):
            if self._file_list._get_job_id_at_row(row) == job_id:
                self._file_list.selectRow(row)
                break
        self._on_remove()

    def _on_open_containing_folder(self, job_id: str) -> None:
        """Open the containing folder in Windows Explorer."""
        jobs = self._file_list.get_all_jobs()
        for job in jobs:
            if job.id == job_id:
                folder = str(job.source_path.parent)
                try:
                    subprocess.Popen(["explorer", folder])
                except OSError as e:
                    self._logger.error(f"Failed to open folder: {e}")
                break

    # ========== Core Logic ==========

    def _import_files(self, paths: list[Path]) -> None:
        """Validate and import files into the queue.

        Args:
            paths: List of file paths to import.
        """
        valid, rejected = FileValidator.filter_valid_files(paths)
        existing_paths = self._file_list.get_all_source_paths()

        added_count = 0
        duplicate_count = 0

        for file_path in valid:
            if FileValidator.is_duplicate(file_path, existing_paths):
                duplicate_count += 1
                continue

            output_path = resolve_output_path(file_path, self._settings)
            job = ConversionJob.from_source(file_path, output_path)
            self._file_list.add_job(job)
            existing_paths.add(file_path)
            added_count += 1
            self._logger.info(f"Added file to queue: {file_path}")

        # Build status message
        parts = []
        if added_count > 0:
            parts.append(f"Added {added_count} file(s)")
        if len(rejected) > 0:
            parts.append(f"{len(rejected)} non-.ts file(s) rejected")
        if duplicate_count > 0:
            parts.append(f"{duplicate_count} duplicate(s) skipped")

        if parts:
            self._show_status_message(" | ".join(parts))

        # Update drop zone placeholder visibility
        self._drop_zone.show_placeholder = self._file_list.get_job_count() == 0
        self._update_ui_state()

    def _start_batch_conversion(self, jobs: list[ConversionJob]) -> None:
        """Start the batch conversion process.

        Creates a ConversionWorker, connects signals, and starts the thread.

        Args:
            jobs: List of pending ConversionJob instances to convert.
        """
        from src.workers.conversion_worker import ConversionWorker
        from src.ui.dialogs import BatchSummaryDialog

        # Detect conflicts
        conflicts = [j for j in jobs if j.output_path.exists()]
        if conflicts:
            from src.ui.dialogs import ConflictPolicyDialog
            from src.models.app_settings import ConflictPolicy
            from src.utils.paths import resolve_conflict_path

            dialog = ConflictPolicyDialog(len(conflicts), self)
            if not dialog.exec():
                return  # User cancelled

            policy = dialog.get_policy()
            if dialog.should_remember():
                self._settings.conflict_policy = policy
                self._settings.save()

            # Apply policy to conflicting jobs
            for job in conflicts:
                if policy == ConflictPolicy.SKIP_ALL:
                    job.set_status(ConversionStatus.SKIPPED)
                elif policy == ConflictPolicy.RENAME_ALL:
                    job.output_path = resolve_conflict_path(job.output_path)
                # OVERWRITE_ALL: no changes needed, FFmpeg -y flag handles it

            # Remove skipped jobs from the processing list
            jobs = [j for j in jobs if j.status == ConversionStatus.PENDING]
            if not jobs:
                self._show_status_message("All files skipped due to conflict policy")
                return

        # Set running state
        self._is_running = True
        self._file_list.set_running(True)
        self._update_ui_state()

        # Create and start worker
        worker = ConversionWorker(jobs, self._settings)
        self._worker = worker

        # Connect signals
        worker.file_started.connect(self._on_worker_file_started)
        worker.progress_updated.connect(self._on_worker_progress_updated)
        worker.file_completed.connect(self._on_worker_file_completed)
        worker.file_failed.connect(self._on_worker_file_failed)
        worker.file_skipped.connect(
            lambda jid: self._file_list.update_job_status(jid, ConversionStatus.SKIPPED)
        )
        worker.batch_completed.connect(self._on_worker_batch_completed)
        worker.batch_cancelled.connect(self._on_worker_batch_completed)
        worker.finished.connect(self._on_worker_finished)

        self._show_status_message(f"Converting {len(jobs)} file(s)...")
        self._logger.info(f"Starting batch conversion: {len(jobs)} files")
        worker.start()

    def _on_worker_finished(self) -> None:
        """Handle worker thread finished signal."""
        self._is_running = False
        self._file_list.set_running(False)
        self._worker = None
        self._update_ui_state()

    # ========== Worker Signal Handlers ==========

    def _on_worker_file_started(self, job_id: str) -> None:
        """Handle worker file_started signal."""
        self._file_list.update_job_status(job_id, ConversionStatus.CONVERTING)

    def _on_worker_progress_updated(self, job_id: str, percent: float) -> None:
        """Handle worker progress_updated signal."""
        self._file_list.update_job_progress(job_id, percent)

    def _on_worker_file_completed(self, job_id: str) -> None:
        """Handle worker file_completed signal."""
        self._file_list.update_job_status(job_id, ConversionStatus.COMPLETE)

    def _on_worker_file_failed(self, job_id: str, error: str) -> None:
        """Handle worker file_failed signal."""
        self._file_list.update_job_status(job_id, ConversionStatus.ERROR, error)

    def _on_worker_batch_completed(self, summary: QueueSummary) -> None:
        """Handle worker batch_completed signal."""
        self._is_running = False
        self._file_list.set_running(False)
        self._update_ui_state()

        # Show summary message
        msg = (
            f"Batch complete: {summary.completed} succeeded, "
            f"{summary.failed} failed, {summary.skipped} skipped"
        )
        self._show_status_message(msg)
        self._logger.info(msg)

    # ========== UI Helpers ==========

    def _update_ui_state(self) -> None:
        """Update enabled/disabled state of all controls based on current state."""
        has_files = self._file_list.get_job_count() > 0
        has_pending = self._file_list.get_pending_count() > 0
        has_selection = len(self._file_list.selectedIndexes()) > 0

        # Toolbar
        self._action_add_files.setEnabled(not self._is_running)
        self._action_remove.setEnabled(not self._is_running and has_selection)
        self._action_clear_all.setEnabled(not self._is_running and has_files)

        # Action buttons
        self._btn_start.setEnabled(
            not self._is_running and has_pending and self._ffmpeg_available
        )
        self._btn_cancel.setEnabled(self._is_running)

        # Browse
        self._btn_browse.setEnabled(not self._is_running)

        # Drop zone & file list drag-drop
        self._drop_zone.setAcceptDrops(not self._is_running)
        self._file_list.setAcceptDrops(not self._is_running)
        self._drop_zone.show_placeholder = not has_files

    def _get_output_display_text(self) -> str:
        """Get the display text for the output directory label."""
        if self._settings.output_directory:
            return self._settings.output_directory
        return "Same as source file"

    def _show_status_message(self, message: str, timeout: int = 5000) -> None:
        """Show a timed message in the status bar.

        Args:
            message: Message to display.
            timeout: Duration in milliseconds (default 5 seconds).
        """
        self._status_bar.showMessage(message, timeout)

    def _restore_geometry(self) -> None:
        """Restore window geometry from saved settings."""
        if self._settings.window_geometry:
            try:
                from PySide6.QtCore import QByteArray

                geometry_bytes = QByteArray.fromHex(
                    self._settings.window_geometry.encode("ascii")
                )
                self.restoreGeometry(geometry_bytes)
            except Exception:
                pass  # Use default geometry

    def closeEvent(self, event: object) -> None:
        """Handle window close - save geometry and check for running conversion."""
        from PySide6.QtGui import QCloseEvent

        if not isinstance(event, QCloseEvent):
            return

        # Check if conversion is running
        if self._is_running:
            result = QMessageBox.warning(
                self,
                "Conversion in Progress",
                "A conversion is currently running.\n\n"
                "If you close now:\n"
                "• The current file conversion will be aborted\n"
                "• Partial output files will be deleted\n"
                "• Remaining files will not be processed",
                QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

            # Cancel the worker
            self._on_cancel()

        # Save window geometry
        geometry_hex = self.saveGeometry().toHex().data().decode("ascii")
        self._settings.window_geometry = geometry_hex
        self._settings.save()

        self._logger.info("Application closing")
        event.accept()

"""Application dialogs: Settings, Conflict Policy, Batch Summary, etc."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from src.models.app_settings import AppSettings, ConflictPolicy, ConverterEngine
from src.models.conversion_job import QueueSummary


class SettingsDialog(QDialog):
    """Application settings dialog.

    Contains:
    - Converter engine selection dropdown
    - Auto-delete source files checkbox
    - Default conflict policy dropdown
    """

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._settings = AppSettings.from_dict(settings.to_dict())  # Work on a copy

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Converter engine selection
        engine_group = QGroupBox("Converter Engine")
        engine_layout = QVBoxLayout()
        engine_label = QLabel("Select the converter engine for .ts to .mp4 conversion:")
        engine_layout.addWidget(engine_label)

        self._cmb_converter_engine = QComboBox()
        self._cmb_converter_engine.setObjectName("cmb_converter_engine")
        self._cmb_converter_engine.addItem(
            "Avidemux (default)", ConverterEngine.AVIDEMUX.value
        )
        self._cmb_converter_engine.addItem("FFmpeg", ConverterEngine.FFMPEG.value)

        # Set current engine
        for i in range(self._cmb_converter_engine.count()):
            if self._cmb_converter_engine.itemData(i) == self._settings.converter_engine.value:
                self._cmb_converter_engine.setCurrentIndex(i)
                break

        engine_layout.addWidget(self._cmb_converter_engine)
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)

        # Auto-delete checkbox
        self._chk_auto_delete = QCheckBox("Auto-delete source files after successful conversion")
        self._chk_auto_delete.setObjectName("chk_auto_delete")
        self._chk_auto_delete.setChecked(self._settings.auto_delete_source)
        layout.addWidget(self._chk_auto_delete)

        # Conflict policy
        policy_group = QGroupBox("Default Conflict Policy")
        policy_layout = QVBoxLayout()
        policy_label = QLabel("When output file already exists:")
        policy_layout.addWidget(policy_label)

        self._cmb_conflict_policy = QComboBox()
        self._cmb_conflict_policy.setObjectName("cmb_conflict_policy")
        self._cmb_conflict_policy.addItem("Ask each time", ConflictPolicy.ASK.value)
        self._cmb_conflict_policy.addItem("Overwrite all", ConflictPolicy.OVERWRITE_ALL.value)
        self._cmb_conflict_policy.addItem("Skip all", ConflictPolicy.SKIP_ALL.value)
        self._cmb_conflict_policy.addItem("Auto-rename (add _1, _2, etc.)", ConflictPolicy.RENAME_ALL.value)

        # Set current policy
        for i in range(self._cmb_conflict_policy.count()):
            if self._cmb_conflict_policy.itemData(i) == self._settings.conflict_policy.value:
                self._cmb_conflict_policy.setCurrentIndex(i)
                break

        policy_layout.addWidget(self._cmb_conflict_policy)
        policy_group.setLayout(policy_layout)
        layout.addWidget(policy_group)

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> AppSettings:
        """Return the modified settings."""
        self._settings.auto_delete_source = self._chk_auto_delete.isChecked()
        policy_value = self._cmb_conflict_policy.currentData()
        self._settings.conflict_policy = ConflictPolicy(policy_value)
        engine_value = self._cmb_converter_engine.currentData()
        self._settings.converter_engine = ConverterEngine(engine_value)
        return self._settings


class ConflictPolicyDialog(QDialog):
    """Pre-batch conflict policy dialog.

    Shown when existing output files are detected before starting conversion.
    """

    def __init__(
        self,
        conflict_count: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("File Conflict Detected")
        self.setMinimumWidth(450)
        self._selected_policy: ConflictPolicy = ConflictPolicy.OVERWRITE_ALL
        self._remember = False

        self._setup_ui(conflict_count)

    def _setup_ui(self, conflict_count: int) -> None:
        layout = QVBoxLayout(self)

        # Warning message
        warning = QLabel(f"⚠️ {conflict_count} output file(s) already exist.")
        warning.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(warning)

        layout.addWidget(QLabel("Choose how to handle existing files:"))

        # Radio buttons
        self._radio_overwrite = QRadioButton("Overwrite all existing files")
        self._radio_skip = QRadioButton("Skip files that already exist")
        self._radio_rename = QRadioButton("Auto-rename (add _1, _2, etc.)")
        self._radio_overwrite.setChecked(True)

        self._button_group = QButtonGroup(self)
        self._button_group.addButton(self._radio_overwrite, 0)
        self._button_group.addButton(self._radio_skip, 1)
        self._button_group.addButton(self._radio_rename, 2)

        layout.addWidget(self._radio_overwrite)
        layout.addWidget(self._radio_skip)
        layout.addWidget(self._radio_rename)

        # Remember checkbox
        self._chk_remember = QCheckBox("Remember this choice for future conversions")
        layout.addWidget(self._chk_remember)

        layout.addStretch()

        # Buttons
        button_bar = QHBoxLayout()
        button_bar.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_continue = QPushButton("Continue")
        btn_continue.setDefault(True)
        btn_cancel.clicked.connect(self.reject)
        btn_continue.clicked.connect(self.accept)
        button_bar.addWidget(btn_cancel)
        button_bar.addWidget(btn_continue)
        layout.addLayout(button_bar)

    def get_policy(self) -> ConflictPolicy:
        """Return the selected conflict policy."""
        checked_id = self._button_group.checkedId()
        if checked_id == 0:
            return ConflictPolicy.OVERWRITE_ALL
        elif checked_id == 1:
            return ConflictPolicy.SKIP_ALL
        else:
            return ConflictPolicy.RENAME_ALL

    def should_remember(self) -> bool:
        """Return whether the user checked 'Remember this choice'."""
        return self._chk_remember.isChecked()


class BatchSummaryDialog(QDialog):
    """Batch conversion summary dialog.

    Shows total, completed, failed, and skipped counts.
    """

    def __init__(
        self,
        summary: QueueSummary,
        log_path: Optional[str] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Conversion Complete")
        self.setMinimumWidth(400)
        self._log_path = log_path

        self._setup_ui(summary)

    def _setup_ui(self, summary: QueueSummary) -> None:
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("✅ Batch conversion finished")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title)

        # Summary details
        details = QVBoxLayout()
        details.addWidget(QLabel(f"Total files:      {summary.total}"))
        details.addWidget(QLabel(f"✅ Completed:     {summary.completed}"))
        details.addWidget(QLabel(f"❌ Failed:        {summary.failed}"))
        if summary.cancelled > 0:
            details.addWidget(QLabel(f"🚫 Cancelled:    {summary.cancelled}"))
        details.addWidget(QLabel(f"⏭️ Skipped:      {summary.skipped}"))
        layout.addLayout(details)

        layout.addStretch()

        # Buttons
        button_bar = QHBoxLayout()
        if self._log_path:
            btn_view_log = QPushButton("View Log")
            btn_view_log.clicked.connect(self._open_log)
            button_bar.addWidget(btn_view_log)
        button_bar.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        button_bar.addWidget(btn_ok)
        layout.addLayout(button_bar)

    def _open_log(self) -> None:
        """Open the log file in the default text editor."""
        if self._log_path:
            try:
                os.startfile(self._log_path)  # type: ignore[attr-defined]
            except OSError:
                pass

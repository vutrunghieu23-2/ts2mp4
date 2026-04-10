"""Drag-and-drop zone widget for importing .ts files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget


def extract_file_paths_from_drop(event: QDropEvent) -> list[str]:
    """Extract file paths from a drop event, supporting both URLs and text (UNC paths).

    Handles:
    - Standard file:// URLs (local files)
    - UNC network paths (\\\\server\\share\\file.ts)
    - Text-based drops containing file paths

    Returns:
        List of file path strings.
    """
    paths: list[str] = []
    mime = event.mimeData()

    # 1. Try URLs first (most common case from Windows Explorer)
    if mime.hasUrls():
        for url in mime.urls():
            if url.isLocalFile():
                local_path = url.toLocalFile()
                if local_path:
                    paths.append(local_path)
            else:
                # Try to extract path from file:// URL for network shares
                url_str = url.toString()
                if url_str.startswith("file:"):
                    # Handle file://server/share or file:////server/share
                    cleaned = url_str.replace("file:", "").lstrip("/")
                    if cleaned and not cleaned[0].isalpha():
                        # Likely a UNC path without drive letter
                        cleaned = "//" + cleaned
                    if cleaned:
                        paths.append(cleaned)

    # 2. If no URLs found, try text (some apps send UNC paths as text)
    if not paths and mime.hasText():
        text = mime.text().strip()
        for line in text.splitlines():
            line = line.strip().strip('"')  # Remove quotes if present
            if line:
                # Check if it looks like a file path (UNC or drive letter)
                if line.startswith("\\\\") or line.startswith("//") or (len(line) > 2 and line[1] == ":"):
                    paths.append(line)

    return paths


class DropZone(QWidget):
    """Widget that accepts drag-and-drop file imports.

    Emits the `files_dropped` signal with a list of file path strings
    when files are dropped onto the widget. Shows a placeholder message
    when the queue is empty, and visual feedback during drag-over.

    Signals:
        files_dropped(list[str]): Emitted with dropped file paths.
    """

    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drag_over = False
        self._show_placeholder = True
        self.setMinimumHeight(100)

    @property
    def show_placeholder(self) -> bool:
        """Whether to show the placeholder message."""
        return self._show_placeholder

    @show_placeholder.setter
    def show_placeholder(self, value: bool) -> None:
        self._show_placeholder = value
        self.update()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drag events with file URLs or text."""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self._drag_over = True
            self.update()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Continue accepting drag events during move."""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Reset visual feedback when drag leaves."""
        self._drag_over = False
        self.update()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file drop - emit paths as signal."""
        self._drag_over = False
        self.update()

        paths = extract_file_paths_from_drop(event)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def paintEvent(self, event: object) -> None:
        """Draw placeholder text and drag-over highlight."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw drag-over highlight
        if self._drag_over:
            painter.fillRect(self.rect(), QColor(70, 130, 180, 40))
            painter.setPen(QColor(70, 130, 180))
            painter.drawRect(self.rect().adjusted(2, 2, -2, -2))

        # Draw placeholder text when queue is empty
        if self._show_placeholder:
            painter.setPen(QColor(150, 150, 150))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Drag and drop .ts files here\nor click \"Add Files\"",
            )

        painter.end()

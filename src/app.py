"""QApplication setup with FFmpeg availability check."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.utils.paths import resolve_ffmpeg_path

if TYPE_CHECKING:
    pass


def create_app() -> tuple[QApplication, MainWindow]:
    """Create and configure the QApplication and MainWindow.

    Performs FFmpeg availability check at startup. If FFmpeg is not
    found, shows an error dialog but still allows the app to launch
    (user might install FFmpeg later).

    Returns:
        A tuple of (QApplication, MainWindow).
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Ts2Mp4")
    app.setOrganizationName("Ts2Mp4")
    app.setApplicationDisplayName("Ts2Mp4 — Video Container Converter")

    # Initialize logger
    logger = setup_logger()
    logger.info("Application starting")

    # Check FFmpeg availability
    ffmpeg_path = resolve_ffmpeg_path()
    if ffmpeg_path is None:
        logger.warning("FFmpeg not found on system")
        QMessageBox.critical(
            None,
            "FFmpeg Not Found",
            "FFmpeg was not found on your system.\n\n"
            "Please install FFmpeg and ensure it is:\n"
            "• In the 'ffmpeg/' folder next to the application, OR\n"
            "• Available on your system PATH\n\n"
            "The application will start, but conversion will not work "
            "until FFmpeg is available.",
        )
    else:
        logger.info(f"FFmpeg found at: {ffmpeg_path}")

    # Create and configure the main window
    window = MainWindow()
    window.set_ffmpeg_available(ffmpeg_path is not None)

    return app, window

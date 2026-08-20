"""Application entry point."""
import sys
import os

# Ensure project root is on the Python path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from video_automator.gui.styles import DARK_THEME
from video_automator.gui.main_window import MainWindow
from video_automator.core.video.ffmpeg_manager import get_ffmpeg_manager


def main():
    # High-DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Video Automator")
    app.setOrganizationName("VideoAutomator")
    app.setApplicationVersion("1.0.0")

    # Set global font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    # Apply dark stylesheet
    app.setStyleSheet(DARK_THEME)

    # Validate FFmpeg early — warn but don't crash
    mgr = get_ffmpeg_manager()
    ok, msg = mgr.validate()
    if not ok:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "FFmpeg Not Found",
            f"{msg}\n\nThe application requires FFmpeg and FFprobe.\n"
            "Please install them and restart.",
        )

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""Background worker: generates a thumbnail image for a video using FFmpeg."""
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import QRunnable, QObject, Signal, Qt


class ThumbnailSignals(QObject):
    """Signals for ThumbnailTask — must be a QObject so they stay alive."""
    done = Signal(str, str)   # (video_path, thumbnail_path)
    error = Signal(str)


class ThumbnailTask(QRunnable):
    """
    Extracts one frame at ~2s from a video and saves it as JPEG.
    Runs inside a QThreadPool for parallel thumbnail generation.

    The ThumbnailSignals object is kept alive by storing it as an attribute
    so Python's GC cannot destroy it while the task is still running.
    """
    THUMB_DIR = Path(tempfile.gettempdir()) / "video_automator_thumbs"

    def __init__(self, video_path: str, size: str = "320x180"):
        super().__init__()
        self._video_path = video_path
        self._size = size
        # Store signals as an attribute — keeps the QObject alive for the
        # duration of the task even if the caller holds no reference to it.
        self.signals = ThumbnailSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            self.THUMB_DIR.mkdir(parents=True, exist_ok=True)

            # Stable, deterministic thumb filename per video path
            key = f"{Path(self._video_path).stem}_{hash(self._video_path) & 0xFFFFFF}"
            thumb_path = str(self.THUMB_DIR / f"{key}.jpg")

            # Return cached thumbnail if it already exists
            if Path(thumb_path).exists():
                try:
                    self.signals.done.emit(self._video_path, thumb_path)
                except RuntimeError:
                    pass
                return

            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                try:
                    self.signals.error.emit("ffmpeg not found")
                except RuntimeError:
                    pass
                return

            result = subprocess.run(
                [
                    ffmpeg, "-y",
                    "-ss", "2",
                    "-i", self._video_path,
                    "-vframes", "1",
                    "-vf", (
                        f"scale={self._size}:force_original_aspect_ratio=decrease,"
                        f"pad={self._size}:(ow-iw)/2:(oh-ih)/2:black"
                    ),
                    "-q:v", "3",
                    thumb_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )

            try:
                if result.returncode == 0 and Path(thumb_path).exists():
                    self.signals.done.emit(self._video_path, thumb_path)
                else:
                    self.signals.error.emit(f"ffmpeg error for: {self._video_path}")
            except RuntimeError:
                pass  # Signal source deleted — app is shutting down

        except Exception as e:
            try:
                self.signals.error.emit(str(e))
            except RuntimeError:
                pass

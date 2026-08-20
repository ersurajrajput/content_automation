"""Step 1 — Video Selection Page."""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QSizePolicy, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from video_automator.models.video_info import VideoInfo
from video_automator.core.video.video_analyzer import VideoAnalyzer, VideoAnalysisError
from video_automator.utils.time_utils import format_seconds_to_hms, format_size_human


VIDEO_FILTERS = "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v);;All Files (*.*)"


class AnalyzeWorker(QThread):
    """Background thread to run FFprobe analysis without blocking the UI."""
    finished = Signal(object, list, list)  # VideoInfo, [AudioTrack], [SubtitleTrack]
    error = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def run(self):
        try:
            analyzer = VideoAnalyzer()
            info, audio, subs = analyzer.analyze(self._path)
            self.finished.emit(info, audio, subs)
        except VideoAnalysisError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Unexpected error analyzing video:\n{e}")


class VideoSelectionPage(QWidget):
    """
    Wizard Step 1: Select a video file and display its metadata.

    Emits `next_requested` with (VideoInfo, [AudioTrack], [SubtitleTrack]) on Next.
    """
    next_requested = Signal(object, list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._video_info = None
        self._audio_tracks = []
        self._subtitle_tracks = []
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(28)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        # Title
        title = QLabel("Select Video")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("Choose a video file to split into clips.")
        subtitle.setObjectName("hint_label")
        layout.addWidget(subtitle)

        # Drop zone
        self._drop_zone = _DropZone()
        self._drop_zone.clicked.connect(self._browse_video)
        layout.addWidget(self._drop_zone)

        # Metadata card (hidden initially)
        self._meta_card = _MetadataCard()
        self._meta_card.hide()
        layout.addWidget(self._meta_card)

        # Status label (analyzing…)
        self._status_label = QLabel("")
        self._status_label.setObjectName("hint_label")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.hide()
        layout.addWidget(self._status_label)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setObjectName("error_label")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        layout.addStretch()

        # Footer buttons
        footer = QHBoxLayout()
        footer.setContentsMargins(48, 12, 48, 20)
        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("btn_primary")
        self._btn_next.setEnabled(False)
        self._btn_next.clicked.connect(self._on_next)
        footer.addStretch()
        footer.addWidget(self._btn_next)
        root.addLayout(footer)

    def _browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", VIDEO_FILTERS
        )
        if path:
            self._load_video(path)

    def _load_video(self, path: str):
        self._video_info = None
        self._audio_tracks = []
        self._subtitle_tracks = []
        self._btn_next.setEnabled(False)
        self._meta_card.hide()
        self._error_label.hide()

        self._status_label.setText(f"Analyzing {Path(path).name}…")
        self._status_label.show()
        self._drop_zone.set_loading(True)

        self._worker = AnalyzeWorker(path)
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_done(self, video_info: VideoInfo, audio_tracks, subtitle_tracks):
        self._video_info = video_info
        self._audio_tracks = audio_tracks
        self._subtitle_tracks = subtitle_tracks

        self._status_label.hide()
        self._drop_zone.set_filename(video_info.filename)
        self._drop_zone.set_loading(False)
        self._meta_card.set_info(video_info, audio_tracks, subtitle_tracks)
        self._meta_card.show()
        self._btn_next.setEnabled(True)

    def _on_analysis_error(self, msg: str):
        self._status_label.hide()
        self._drop_zone.set_loading(False)
        self._drop_zone.reset()
        self._error_label.setText(f"⚠  {msg}")
        self._error_label.show()

    def _on_next(self):
        if self._video_info:
            self.next_requested.emit(
                self._video_info, self._audio_tracks, self._subtitle_tracks
            )

    # Drag-and-drop
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            ext = Path(path).suffix.lower()
            if ext in {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}:
                self._load_video(path)
            else:
                self._error_label.setText(
                    f"⚠  Unsupported file format: {ext}. Please select MP4, MKV, MOV, AVI, WebM, or M4V."
                )
                self._error_label.show()


class _DropZone(QWidget):
    """Clickable drag-and-drop target for video files."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filename = None
        self._loading = False
        self.setFixedHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        self._icon = QLabel("🎬")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("font-size: 40px;")
        layout.addWidget(self._icon)

        self._primary = QLabel("Click to browse or drag & drop a video")
        self._primary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._primary.setStyleSheet("color: #9ca3af; font-size: 14px;")
        layout.addWidget(self._primary)

        self._secondary = QLabel("MP4  MKV  MOV  AVI  WebM  M4V")
        self._secondary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._secondary.setStyleSheet("color: #4b5563; font-size: 11px; letter-spacing: 1.5px;")
        layout.addWidget(self._secondary)

        self.setStyleSheet("""
            _DropZone, QWidget#drop_zone {
                background-color: #14141c;
                border: 2px dashed #2d2d45;
                border-radius: 14px;
            }
        """)
        self.setObjectName("drop_zone")

    def set_filename(self, filename: str):
        self._filename = filename
        self._loading = False
        self._icon.setText("✅")
        self._primary.setStyleSheet("color: #c4b5fd; font-size: 14px; font-weight: 600;")
        self._primary.setText(filename)
        self._secondary.setText("Click to choose a different video")
        self.setStyleSheet("""
            QWidget#drop_zone {
                background-color: #1a1030;
                border: 2px dashed #7c3aed;
                border-radius: 14px;
            }
        """)

    def set_loading(self, loading: bool):
        self._loading = loading
        if loading:
            self._icon.setText("⏳")
            self._primary.setText("Analyzing video…")
            self._primary.setStyleSheet("color: #a78bfa; font-size: 14px;")

    def reset(self):
        self._filename = None
        self._loading = False
        self._icon.setText("🎬")
        self._primary.setText("Click to browse or drag & drop a video")
        self._primary.setStyleSheet("color: #9ca3af; font-size: 14px;")
        self._secondary.setText("MP4  MKV  MOV  AVI  WebM  M4V")
        self.setStyleSheet("""
            QWidget#drop_zone {
                background-color: #14141c;
                border: 2px dashed #2d2d45;
                border-radius: 14px;
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()


class _MetadataCard(QWidget):
    """Displays video metadata in a styled card."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card_elevated")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("Video Information")
        header.setObjectName("section_label")
        layout.addWidget(header)

        grid = QHBoxLayout()
        self._left = QVBoxLayout()
        self._right = QVBoxLayout()
        self._left.setSpacing(8)
        self._right.setSpacing(8)
        grid.addLayout(self._left)
        grid.addSpacing(40)
        grid.addLayout(self._right)
        grid.addStretch()
        layout.addLayout(grid)

        self._rows_left = {}
        self._rows_right = {}
        left_fields = ["Name", "File Size", "Duration"]
        right_fields = ["Resolution", "FPS", "Video Codec", "Audio Codec"]
        for f in left_fields:
            self._rows_left[f] = self._make_row(f, self._left)
        for f in right_fields:
            self._rows_right[f] = self._make_row(f, self._right)

    def _make_row(self, label: str, parent_layout: QVBoxLayout):
        row = QHBoxLayout()
        lbl = QLabel(label + ":")
        lbl.setObjectName("section_label")
        lbl.setFixedWidth(100)
        val = QLabel("—")
        val.setObjectName("value_label")
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        parent_layout.addLayout(row)
        return val

    def set_info(self, info: VideoInfo, audio_tracks, subtitle_tracks):
        from video_automator.utils.time_utils import format_size_human
        self._rows_left["Name"].setText(info.filename)
        self._rows_left["File Size"].setText(format_size_human(info.size_bytes))
        self._rows_left["Duration"].setText(format_seconds_to_hms(info.duration_seconds))
        self._rows_right["Resolution"].setText(info.resolution_str)
        self._rows_right["FPS"].setText(info.fps_str)
        self._rows_right["Video Codec"].setText(info.video_codec or "—")
        self._rows_right["Audio Codec"].setText(info.audio_codec or "—")

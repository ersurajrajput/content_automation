"""Step 9 — Processing Page."""
import time
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QScrollArea, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer

from video_automator.models.clip_settings import ClipSettings
from video_automator.core.video.video_processor import VideoProcessor, ClipResult
from video_automator.utils.time_utils import format_seconds_to_hms


class ProcessingPage(QWidget):
    """
    Wizard Step 9: Live progress display during clip generation.
    Shows current clip, overall progress, ETA, and Cancel button.
    """
    finished = Signal(list)    # List[ClipResult]
    cancelled = Signal(list)   # List[ClipResult] so far

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processor: VideoProcessor = None
        self._results: List[ClipResult] = []
        self._total = 0
        self._completed = 0
        self._start_time = 0.0
        self._cancelled_flag = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(28)

        title = QLabel("Generating Clips…")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # Source card
        self._source_card = QFrame()
        self._source_card.setObjectName("info_card")
        source_layout = QHBoxLayout(self._source_card)
        src_icon = QLabel("📂")
        src_icon.setStyleSheet("font-size: 22px;")
        source_layout.addWidget(src_icon)
        self._source_lbl = QLabel("Source: —")
        self._source_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        source_layout.addWidget(self._source_lbl)
        source_layout.addStretch()
        layout.addWidget(self._source_card)

        # Progress card
        prog_card = QFrame()
        prog_card.setObjectName("card_elevated")
        prog_layout = QVBoxLayout(prog_card)
        prog_layout.setSpacing(16)

        # Current clip
        self._current_lbl = QLabel("Preparing…")
        self._current_lbl.setStyleSheet(
            "color: #c4b5fd; font-size: 14px; font-weight: 600;"
        )
        prog_layout.addWidget(self._current_lbl)

        # Timestamps
        self._timestamp_lbl = QLabel("")
        self._timestamp_lbl.setObjectName("hint_label")
        prog_layout.addWidget(self._timestamp_lbl)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(16)
        self._progress_bar.setFormat("")
        prog_layout.addWidget(self._progress_bar)

        # Count row
        count_row = QHBoxLayout()
        self._count_lbl = QLabel("0 / 0 clips")
        self._count_lbl.setStyleSheet("color: #e8e8f0; font-size: 14px; font-weight: 600;")
        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setStyleSheet("color: #a78bfa; font-size: 14px; font-weight: 700;")
        count_row.addWidget(self._count_lbl)
        count_row.addStretch()
        count_row.addWidget(self._pct_lbl)
        prog_layout.addLayout(count_row)

        # Speed / ETA
        self._eta_lbl = QLabel("")
        self._eta_lbl.setObjectName("hint_label")
        prog_layout.addWidget(self._eta_lbl)

        # Status message
        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("hint_label")
        self._status_lbl.setWordWrap(True)
        prog_layout.addWidget(self._status_lbl)

        layout.addWidget(prog_card)
        layout.addStretch()

        # Cancel button
        cancel_row = QHBoxLayout()
        self._btn_cancel = QPushButton("Cancel Processing")
        self._btn_cancel.setObjectName("btn_danger")
        self._btn_cancel.setFixedWidth(200)
        self._btn_cancel.clicked.connect(self._on_cancel)
        cancel_row.addStretch()
        cancel_row.addWidget(self._btn_cancel)
        cancel_row.addStretch()
        layout.addLayout(cancel_row)

    def start(self, settings: ClipSettings):
        """Start the background processor."""
        self._cancelled_flag = False
        self._results = []
        self._completed = 0
        self._total = settings.total_clips
        self._start_time = time.time()

        self._progress_bar.setValue(0)
        self._count_lbl.setText(f"0 / {self._total} clips")
        self._pct_lbl.setText("0%")
        self._eta_lbl.setText("")
        self._status_lbl.setText("")
        self._current_lbl.setText("Preparing…")
        self._timestamp_lbl.setText("")
        self._source_lbl.setText(
            f"Source: {settings.source_video.filename if settings.source_video else '—'}"
        )
        self._btn_cancel.setEnabled(True)

        self._processor = VideoProcessor(settings)
        self._processor.progress_changed.connect(self._on_progress)
        self._processor.clip_started.connect(self._on_clip_started)
        self._processor.clip_finished.connect(self._on_clip_finished)
        self._processor.status_message.connect(self._on_status)
        self._processor.speed_updated.connect(self._on_speed)
        self._processor.error_occurred.connect(self._on_error)
        self._processor.finished_processing.connect(self._on_done)
        self._processor.start()

    def _on_progress(self, completed: int, total: int):
        self._completed = completed
        self._total = total
        pct = int(completed / total * 100) if total else 0
        self._progress_bar.setValue(pct)
        self._count_lbl.setText(f"{completed} / {total} clips")
        self._pct_lbl.setText(f"{pct}%")

    def _on_clip_started(self, clip_num: int, filename: str, start_sec: float, end_sec: float):
        self._current_lbl.setText(f"Current: {filename}")
        self._timestamp_lbl.setText(
            f"  {format_seconds_to_hms(start_sec)} → {format_seconds_to_hms(end_sec)}"
        )

    def _on_clip_finished(self, clip_num: int, filename: str, success: bool):
        if not success:
            self._status_lbl.setText(f"⚠  Failed: {filename}")

    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)

    def _on_speed(self, info: str):
        self._eta_lbl.setText(info)

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"⚠  Error: {msg[:200]}")

    def _on_done(self, results: list):
        self._results = results
        self._btn_cancel.setEnabled(False)
        if self._cancelled_flag:
            self.cancelled.emit(results)
        else:
            self._current_lbl.setText("✅ Processing complete!")
            self._progress_bar.setValue(100)
            self._pct_lbl.setText("100%")
            self._count_lbl.setText(f"{len(results)} / {self._total} clips")
            self.finished.emit(results)

    def _on_cancel(self):
        reply = QMessageBox.question(
            self,
            "Cancel Processing?",
            "Are you sure you want to cancel?\n\nAlready-generated clips will be kept.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._cancelled_flag = True
            self._btn_cancel.setEnabled(False)
            self._current_lbl.setText("Cancelling…")
            if self._processor:
                self._processor.cancel()

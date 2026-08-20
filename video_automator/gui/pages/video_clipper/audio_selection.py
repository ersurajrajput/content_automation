"""Step 2 — Audio / Language Selection Page with Audio Preview."""
import shutil
import subprocess
import tempfile
import os
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QRadioButton, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QThread

from video_automator.models.audio_track import AudioTrack
from video_automator.core.video.ffmpeg_manager import get_ffmpeg_manager


class AudioPreviewWorker(QThread):
    """Extracts a 15-second audio sample to a temp file for preview."""
    ready = Signal(str)   # temp wav path
    error = Signal(str)

    def __init__(self, video_path: str, audio_index: int):
        super().__init__()
        self._video_path = video_path
        self._audio_index = audio_index
        self._temp_path = ""

    def run(self):
        try:
            mgr = get_ffmpeg_manager()
            fd, path = tempfile.mkstemp(suffix=".wav", prefix="va_preview_")
            os.close(fd)
            self._temp_path = path

            proc = mgr.start_ffmpeg([
                "-ss", "0",
                "-i", self._video_path,
                "-t", "15",
                "-map", f"0:a:{self._audio_index}",
                "-ac", "2",
                "-ar", "44100",
                "-vn",
                "-y", path,
            ])
            proc.wait(timeout=30)
            if proc.returncode == 0:
                self.ready.emit(path)
            else:
                self.error.emit("Failed to extract audio sample.")
        except Exception as e:
            self.error.emit(str(e))

    def cleanup(self):
        if self._temp_path and os.path.exists(self._temp_path):
            try:
                os.remove(self._temp_path)
            except Exception:
                pass


class AudioSelectionPage(QWidget):
    """
    Wizard Step 2: Pick which audio stream to include in generated clips.
    Each track has a ▶ Preview button to listen before selecting.
    Auto-selects if only one audio track exists.
    """
    next_requested = Signal(object)   # AudioTrack
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: List[AudioTrack] = []
        self._selected: Optional[AudioTrack] = None
        self._video_path = ""
        self._preview_proc: Optional[subprocess.Popen] = None
        self._preview_worker: Optional[AudioPreviewWorker] = None
        self._preview_temp: str = ""
        self._active_preview_btn: Optional[QPushButton] = None
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

        title = QLabel("Select Audio Track")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self._subtitle = QLabel(
            "Choose which audio language / track to include in your clips.\n"
            "Use the ▶ Preview button to listen to each track before selecting."
        )
        self._subtitle.setObjectName("hint_label")
        layout.addWidget(self._subtitle)

        # Preview status bar
        self._preview_bar = QFrame()
        self._preview_bar.setObjectName("info_card")
        pb_layout = QHBoxLayout(self._preview_bar)
        pb_layout.setContentsMargins(12, 8, 12, 8)
        self._preview_icon = QLabel("🔊")
        self._preview_icon.setStyleSheet("font-size: 18px;")
        pb_layout.addWidget(self._preview_icon)
        self._preview_status = QLabel("Click ▶ next to any track to preview 15 seconds of audio.")
        self._preview_status.setStyleSheet("color: #9ca3af; font-size: 12px;")
        pb_layout.addWidget(self._preview_status, 1)
        self._btn_stop = QPushButton("⏹ Stop")
        self._btn_stop.setObjectName("btn_danger")
        self._btn_stop.setFixedWidth(80)
        self._btn_stop.setFixedHeight(28)
        self._btn_stop.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        self._btn_stop.clicked.connect(self._stop_preview)
        self._btn_stop.hide()
        pb_layout.addWidget(self._btn_stop)
        layout.addWidget(self._preview_bar)

        # Track list card
        self._card = QFrame()
        self._card.setObjectName("card_elevated")
        self._card_layout = QVBoxLayout(self._card)
        self._card_layout.setSpacing(4)
        layout.addWidget(self._card)

        self._btn_group = QButtonGroup(self)
        self._btn_group.buttonClicked.connect(self._on_selection_changed)

        layout.addStretch()

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(48, 12, 48, 20)
        btn_back = QPushButton("← Back")
        btn_back.setObjectName("btn_secondary")
        btn_back.clicked.connect(self._on_back)
        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("btn_primary")
        self._btn_next.setEnabled(False)
        self._btn_next.clicked.connect(self._on_next)
        footer.addWidget(btn_back)
        footer.addStretch()
        footer.addWidget(self._btn_next)
        root.addLayout(footer)

    def load_tracks(self, tracks: List[AudioTrack], video_path: str = ""):
        """Populate audio options. Auto-selects single track."""
        self._stop_preview()
        self._tracks = tracks
        self._video_path = video_path

        # Clear previous widgets
        for btn in self._btn_group.buttons():
            self._btn_group.removeButton(btn)
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        header = QLabel("Available Audio Tracks")
        header.setObjectName("section_label")
        self._card_layout.addWidget(header)
        self._card_layout.addSpacing(8)

        if not tracks:
            self._card_layout.addWidget(QLabel("No audio tracks found."))
            return

        # Detect ffplay availability for preview button
        has_ffplay = bool(shutil.which("ffplay"))

        for track in tracks:
            wrapper = self._make_track_row(track, has_ffplay)
            self._btn_group.addButton(
                wrapper.findChild(QRadioButton), track.index
            )
            self._card_layout.addWidget(wrapper)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            self._card_layout.addWidget(sep)

        # Auto-select single track
        if len(tracks) == 1:
            radio = self._btn_group.button(0)
            if radio:
                radio.setChecked(True)
            self._selected = tracks[0]
            self._btn_next.setEnabled(True)
            self._subtitle.setText(
                "Single audio track detected — automatically selected: "
                f"<b>{tracks[0].display_name}</b>"
            )

    def _make_track_row(self, track: AudioTrack, has_ffplay: bool) -> QWidget:
        """Build one row: [radio] [info] [▶ Preview]"""
        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget:hover { background-color: #1e1e2e; border-radius: 8px; }")

        row = QHBoxLayout(wrapper)
        row.setContentsMargins(8, 8, 8, 8)
        row.setSpacing(12)

        radio = QRadioButton()
        radio.setObjectName(f"audio_radio_{track.index}")
        row.addWidget(radio)

        # Track info
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_lbl = QLabel(track.display_name)
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #e8e8f0;")
        info_layout.addWidget(name_lbl)

        detail_parts = []
        if track.codec:
            detail_parts.append(track.codec.upper())
        if track.channels:
            detail_parts.append(f"{track.channels}ch")
        if track.sample_rate:
            detail_parts.append(f"{track.sample_rate // 1000}kHz")
        if track.language_code:
            detail_parts.append(f"[{track.language_code.upper()}]")

        detail_lbl = QLabel("  ·  ".join(detail_parts) if detail_parts else "—")
        detail_lbl.setObjectName("hint_label")
        info_layout.addWidget(detail_lbl)

        row.addWidget(info, 1)

        # Preview button
        if has_ffplay and self._video_path:
            btn_preview = QPushButton("▶  Preview")
            btn_preview.setObjectName("btn_preset")
            btn_preview.setFixedWidth(100)
            btn_preview.setFixedHeight(32)
            btn_preview.setToolTip("Preview 15 seconds of this audio track")
            # Capture track by default arg
            btn_preview.clicked.connect(
                lambda checked=False, t=track, b=btn_preview: self._preview_track(t, b)
            )
            row.addWidget(btn_preview)
        elif not has_ffplay:
            no_preview = QLabel("ffplay not found")
            no_preview.setStyleSheet("color: #374151; font-size: 10px;")
            row.addWidget(no_preview)

        return wrapper

    def _preview_track(self, track: AudioTrack, btn: QPushButton):
        """Start audio preview for this track."""
        # Stop any existing preview first
        self._stop_preview()

        self._active_preview_btn = btn
        btn.setText("⏳ Loading…")
        btn.setEnabled(False)
        self._preview_status.setText(f"Loading preview for: {track.display_name}…")
        self._btn_stop.show()

        # Extract audio sample in background, then play
        worker = AudioPreviewWorker(self._video_path, track.index)
        worker.ready.connect(lambda path, t=track: self._play_audio(path, t))
        worker.error.connect(self._on_preview_error)
        self._preview_worker = worker
        worker.start()

    def _play_audio(self, wav_path: str, track: AudioTrack):
        """Play the extracted audio sample using ffplay."""
        self._preview_temp = wav_path
        try:
            ffplay = shutil.which("ffplay")
            if not ffplay:
                self._on_preview_error("ffplay not found.")
                return

            self._preview_proc = subprocess.Popen(
                [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", wav_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if self._active_preview_btn:
                self._active_preview_btn.setText("🔊 Playing…")
                self._active_preview_btn.setEnabled(True)

            self._preview_status.setText(
                f"🔊  Playing: {track.display_name}  ·  15 second preview"
            )
            self._preview_icon.setText("🔊")

            # Poll for completion
            self._poll_playback(track)

        except Exception as e:
            self._on_preview_error(str(e))

    def _poll_playback(self, track: AudioTrack):
        """Check every 500ms if ffplay has finished."""
        from PySide6.QtCore import QTimer
        def check():
            if self._preview_proc and self._preview_proc.poll() is not None:
                self._on_playback_finished(track)
            elif self._preview_proc:
                QTimer.singleShot(500, check)
        QTimer.singleShot(500, check)

    def _on_playback_finished(self, track: AudioTrack):
        self._preview_status.setText(
            f"✓  Preview finished: {track.display_name}  ·  Click ▶ to replay."
        )
        self._preview_icon.setText("✅")
        self._btn_stop.hide()
        if self._active_preview_btn:
            self._active_preview_btn.setText("▶  Preview")
            self._active_preview_btn.setEnabled(True)
        # Clean up temp file
        if self._preview_worker:
            self._preview_worker.cleanup()

    def _stop_preview(self):
        """Kill any running ffplay process."""
        if self._preview_proc:
            try:
                self._preview_proc.kill()
                self._preview_proc = None
            except Exception:
                pass
        if self._preview_worker:
            self._preview_worker.cleanup()
            self._preview_worker = None
        self._btn_stop.hide()
        if self._active_preview_btn:
            self._active_preview_btn.setText("▶  Preview")
            self._active_preview_btn.setEnabled(True)
            self._active_preview_btn = None
        self._preview_status.setText(
            "Click ▶ next to any track to preview 15 seconds of audio."
        )
        self._preview_icon.setText("🔊")

    def _on_preview_error(self, msg: str):
        self._preview_status.setText(f"⚠  Preview error: {msg}")
        self._preview_icon.setText("⚠")
        self._btn_stop.hide()
        if self._active_preview_btn:
            self._active_preview_btn.setText("▶  Preview")
            self._active_preview_btn.setEnabled(True)
            self._active_preview_btn = None

    def _on_selection_changed(self, button):
        idx = self._btn_group.id(button)
        for t in self._tracks:
            if t.index == idx:
                self._selected = t
                break
        self._btn_next.setEnabled(True)

    def _on_back(self):
        self._stop_preview()
        self.back_requested.emit()

    def _on_next(self):
        self._stop_preview()
        if self._selected:
            self.next_requested.emit(self._selected)

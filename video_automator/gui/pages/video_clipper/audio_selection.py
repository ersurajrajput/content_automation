"""Step 2 — Audio / Language Selection Page."""
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QRadioButton, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from video_automator.models.audio_track import AudioTrack


class AudioSelectionPage(QWidget):
    """
    Wizard Step 2: Pick which audio stream to include in generated clips.
    Auto-selects if only one audio track exists.
    """
    next_requested = Signal(object)   # AudioTrack
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: List[AudioTrack] = []
        self._selected: AudioTrack = None
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
        title = QLabel("Select Audio Track")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self._subtitle = QLabel("Choose which audio language / track to include in your clips.")
        self._subtitle.setObjectName("hint_label")
        layout.addWidget(self._subtitle)

        # Options card
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
        btn_back.clicked.connect(self.back_requested.emit)
        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("btn_primary")
        self._btn_next.setEnabled(False)
        self._btn_next.clicked.connect(self._on_next)
        footer.addWidget(btn_back)
        footer.addStretch()
        footer.addWidget(self._btn_next)
        root.addLayout(footer)

    def load_tracks(self, tracks: List[AudioTrack]):
        """Populate audio options. Auto-selects single track."""
        self._tracks = tracks
        # Clear previous
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

        for track in tracks:
            radio = QRadioButton()
            row = _AudioTrackRow(track)
            radio.setObjectName(f"audio_radio_{track.index}")

            row_container = QHBoxLayout()
            row_container.setSpacing(12)
            row_container.addWidget(radio)
            row_container.addWidget(row)
            row_container.addStretch()

            wrapper = QWidget()
            wrapper.setLayout(row_container)
            wrapper.setStyleSheet("""
                QWidget:hover {
                    background-color: #1e1e2e;
                    border-radius: 8px;
                }
            """)
            self._btn_group.addButton(radio, track.index)
            self._card_layout.addWidget(wrapper)

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            self._card_layout.addWidget(sep)

        # Auto-select single track
        if len(tracks) == 1:
            self._btn_group.button(0).setChecked(True)
            self._selected = tracks[0]
            self._btn_next.setEnabled(True)
            self._subtitle.setText(
                f"Single audio track detected. Automatically selected: "
                f"<b>{tracks[0].display_name}</b>"
            )

    def _on_selection_changed(self, button):
        idx = self._btn_group.id(button)
        for t in self._tracks:
            if t.index == idx:
                self._selected = t
                break
        self._btn_next.setEnabled(True)

    def _on_next(self):
        if self._selected:
            self.next_requested.emit(self._selected)


class _AudioTrackRow(QWidget):
    def __init__(self, track: AudioTrack, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(2)

        name = QLabel(track.display_name)
        name.setStyleSheet("font-size: 14px; font-weight: 600; color: #e8e8f0;")
        layout.addWidget(name)

        detail = QLabel(track.detail_str)
        detail.setObjectName("hint_label")
        layout.addWidget(detail)

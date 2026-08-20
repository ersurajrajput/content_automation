"""Step 3 — Subtitle Selection Page."""
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QRadioButton, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from video_automator.models.subtitle_track import SubtitleTrack


class SubtitleSelectionPage(QWidget):
    """
    Wizard Step 3: Pick which subtitle track to use (or none).
    """
    next_requested = Signal(object)   # SubtitleTrack or None
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: List[SubtitleTrack] = []
        self._selected: Optional[SubtitleTrack] = None
        self._no_sub_selected = False
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(28)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        title = QLabel("Select Subtitle")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self._subtitle_lbl = QLabel("Choose which subtitle track to embed or burn into clips.")
        self._subtitle_lbl.setObjectName("hint_label")
        layout.addWidget(self._subtitle_lbl)

        self._card = QFrame()
        self._card.setObjectName("card_elevated")
        self._card_layout = QVBoxLayout(self._card)
        layout.addWidget(self._card)
        layout.addStretch()

        footer = QHBoxLayout()
        footer.setContentsMargins(48, 12, 48, 20)
        btn_back = QPushButton("← Back")
        btn_back.setObjectName("btn_secondary")
        btn_back.clicked.connect(self.back_requested.emit)
        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("btn_primary")
        self._btn_next.clicked.connect(self._on_next)
        footer.addWidget(btn_back)
        footer.addStretch()
        footer.addWidget(self._btn_next)
        root.addLayout(footer)

    def load_tracks(self, tracks: List[SubtitleTrack]):
        self._tracks = tracks
        self._selected = None
        self._no_sub_selected = False

        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        header = QLabel("Subtitle Streams")
        header.setObjectName("section_label")
        self._card_layout.addWidget(header)
        self._card_layout.addSpacing(8)

        self._btn_group = QButtonGroup(self)
        self._btn_group.buttonClicked.connect(self._on_selection)

        # "No subtitles" option
        no_sub_radio = QRadioButton("No subtitles")
        no_sub_radio.setChecked(True)
        no_sub_radio.setStyleSheet("font-size: 13px; color: #9ca3af; padding: 6px 0;")
        self._btn_group.addButton(no_sub_radio, -1)
        self._card_layout.addWidget(no_sub_radio)
        self._no_sub_selected = True

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        self._card_layout.addWidget(sep)

        if not tracks:
            info = QLabel("No subtitle streams detected in this video.")
            info.setObjectName("hint_label")
            self._card_layout.addWidget(info)
            return

        for track in tracks:
            radio = QRadioButton()
            row = _SubtitleRow(track)

            row_container = QHBoxLayout()
            row_container.setSpacing(12)
            row_container.addWidget(radio)
            row_container.addWidget(row)
            row_container.addStretch()

            wrapper = QWidget()
            wrapper.setLayout(row_container)
            self._btn_group.addButton(radio, track.index)
            self._card_layout.addWidget(wrapper)

    def _on_selection(self, button):
        bid = self._btn_group.id(button)
        if bid == -1:
            self._selected = None
            self._no_sub_selected = True
        else:
            self._no_sub_selected = False
            self._selected = next((t for t in self._tracks if t.index == bid), None)

    def _on_next(self):
        self.next_requested.emit(self._selected)


class _SubtitleRow(QWidget):
    def __init__(self, track: SubtitleTrack, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(2)

        badges = []
        if track.is_default:
            badges.append("[Default]")
        if track.is_forced:
            badges.append("[Forced]")
        if track.is_image_based:
            badges.append("[Image-based]")

        name = QLabel(track.display_name + ("  " + " ".join(badges) if badges else ""))
        name.setStyleSheet("font-size: 14px; font-weight: 600; color: #e8e8f0;")
        layout.addWidget(name)

        detail = QLabel(f"Format: {track.codec or 'unknown'}  |  Language: {track.language_code or '—'}")
        detail.setObjectName("hint_label")
        layout.addWidget(detail)

        if track.is_image_based:
            warn = QLabel("⚠  Image-based subtitle — cannot be burned into video")
            warn.setObjectName("error_label")
            layout.addWidget(warn)

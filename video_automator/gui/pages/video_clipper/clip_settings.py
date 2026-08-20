"""Step 5 — Clip Duration & Subtitle Output Mode."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QCheckBox, QButtonGroup, QRadioButton, QFrame,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from video_automator.models.clip_settings import SubtitleMode
from video_automator.utils.time_utils import format_seconds_to_hms


PRESETS = [
    ("30s", 30),
    ("60s", 60),
    ("90s", 90),
    ("2 min", 120),
    ("5 min", 300),
]


class ClipSettingsPage(QWidget):
    """
    Wizard Step 5: Configure clip duration, subtitle output mode, and partial clip option.
    """
    next_requested = Signal(float, bool, object)  # duration_secs, include_partial, SubtitleMode
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_duration = 0.0
        self._has_subtitle = False
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
        layout.setSpacing(32)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        # ── Title ──
        title = QLabel("Clip Settings")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # ── Duration card ──
        dur_card = QFrame()
        dur_card.setObjectName("card_elevated")
        dur_layout = QVBoxLayout(dur_card)
        dur_layout.setSpacing(16)

        dur_header = QLabel("Clip Duration")
        dur_header.setObjectName("section_label")
        dur_layout.addWidget(dur_header)

        # Presets
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        self._preset_group = QButtonGroup(self)
        for label, secs in PRESETS:
            btn = QPushButton(label)
            btn.setObjectName("btn_preset")
            btn.setCheckable(True)
            btn.setFixedWidth(72)
            self._preset_group.addButton(btn, secs)
            preset_row.addWidget(btn)
        preset_row.addStretch()
        dur_layout.addLayout(preset_row)
        self._preset_group.buttonClicked.connect(self._on_preset)

        # Manual input
        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        lbl_min = QLabel("Minutes:")
        lbl_min.setObjectName("hint_label")
        self._spin_min = QSpinBox()
        self._spin_min.setRange(0, 999)
        self._spin_min.setValue(1)
        self._spin_min.setFixedWidth(80)
        self._spin_min.valueChanged.connect(self._on_manual_change)

        lbl_sec = QLabel("Seconds:")
        lbl_sec.setObjectName("hint_label")
        self._spin_sec = QSpinBox()
        self._spin_sec.setRange(0, 59)
        self._spin_sec.setValue(0)
        self._spin_sec.setFixedWidth(80)
        self._spin_sec.valueChanged.connect(self._on_manual_change)

        input_row.addWidget(lbl_min)
        input_row.addWidget(self._spin_min)
        input_row.addSpacing(16)
        input_row.addWidget(lbl_sec)
        input_row.addWidget(self._spin_sec)
        input_row.addStretch()
        dur_layout.addLayout(input_row)

        # Summary
        self._dur_summary = QLabel("")
        self._dur_summary.setStyleSheet("color: #a78bfa; font-size: 13px; font-weight: 500;")
        dur_layout.addWidget(self._dur_summary)

        # Error
        self._dur_error = QLabel("")
        self._dur_error.setObjectName("error_label")
        dur_layout.addWidget(self._dur_error)

        # Partial clip
        self._check_partial = QCheckBox("Include final partial clip (if video doesn't divide evenly)")
        self._check_partial.setChecked(True)
        dur_layout.addWidget(self._check_partial)

        layout.addWidget(dur_card)

        # ── Subtitle Output Mode card ──
        self._sub_card = QFrame()
        self._sub_card.setObjectName("card_elevated")
        sub_layout = QVBoxLayout(self._sub_card)
        sub_layout.setSpacing(12)

        sub_header = QLabel("Subtitle Output")
        sub_header.setObjectName("section_label")
        sub_layout.addWidget(sub_header)

        self._sub_group = QButtonGroup(self)
        options = [
            (SubtitleMode.NO_SUBTITLES, "No subtitles", "Don't include subtitles in clips"),
            (SubtitleMode.EMBEDDED, "Embedded subtitles", "Keep as a subtitle stream (soft subtitles)"),
            (SubtitleMode.BURNED, "Burn subtitles into video", "Render subtitles directly onto frames"),
        ]
        for mode, label, hint in options:
            row_w = QWidget()
            row_layout = QVBoxLayout(row_w)
            row_layout.setContentsMargins(0, 4, 0, 4)
            radio = QRadioButton(label)
            radio.setStyleSheet("font-size: 13px;")
            hint_lbl = QLabel(hint)
            hint_lbl.setObjectName("hint_label")
            row_layout.addWidget(radio)
            row_layout.addWidget(hint_lbl)
            self._sub_group.addButton(radio, list(SubtitleMode).index(mode))
            sub_layout.addWidget(row_w)

        self._sub_group.button(0).setChecked(True)
        layout.addWidget(self._sub_card)
        layout.addStretch()

        # Footer
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

        # Init
        self._update_summary()

    def load(self, video_duration: float, has_subtitle: bool):
        self._video_duration = video_duration
        self._has_subtitle = has_subtitle
        self._sub_card.setVisible(has_subtitle)
        self._update_summary()

    def _current_duration(self) -> float:
        return self._spin_min.value() * 60 + self._spin_sec.value()

    def _on_preset(self, button):
        secs = self._preset_group.id(button)
        mins, sec = divmod(secs, 60)
        self._spin_min.blockSignals(True)
        self._spin_sec.blockSignals(True)
        self._spin_min.setValue(mins)
        self._spin_sec.setValue(sec)
        self._spin_min.blockSignals(False)
        self._spin_sec.blockSignals(False)
        self._update_summary()

    def _on_manual_change(self):
        # Deselect preset buttons when user types manually
        checked = self._preset_group.checkedButton()
        if checked:
            self._preset_group.setExclusive(False)
            checked.setChecked(False)
            self._preset_group.setExclusive(True)
        self._update_summary()

    def _update_summary(self):
        dur = self._current_duration()
        self._dur_error.setText("")
        if dur <= 0:
            self._dur_summary.setText("Please enter a valid clip duration.")
            self._btn_next.setEnabled(False)
            return
        if self._video_duration > 0 and dur > self._video_duration:
            self._dur_error.setText(
                f"⚠  Clip duration exceeds video duration "
                f"({format_seconds_to_hms(self._video_duration)})"
            )
            self._btn_next.setEnabled(False)
            return

        clips = 0
        if self._video_duration > 0:
            import math
            full = int(self._video_duration // dur)
            remainder = self._video_duration % dur
            include_partial = self._check_partial.isChecked()
            clips = full + (1 if include_partial and remainder > 0.5 else 0)

        self._dur_summary.setText(
            f"Duration: {format_seconds_to_hms(dur)}  ·  "
            + (f"Expected clips: {clips}" if clips else "")
        )
        self._btn_next.setEnabled(True)

    def _on_next(self):
        dur = self._current_duration()
        include_partial = self._check_partial.isChecked()
        bid = self._sub_group.checkedId()
        mode = list(SubtitleMode)[bid]
        self.next_requested.emit(dur, include_partial, mode)

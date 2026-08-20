"""Step 8 — Review & Confirm Page."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout,
)
from PySide6.QtCore import Qt, Signal

from video_automator.models.clip_settings import ClipSettings, SubtitleMode
from video_automator.utils.time_utils import format_seconds_to_hms
from video_automator.utils.disk_utils import estimate_clipping_space
from video_automator.utils.time_utils import format_size_human



class ReviewPage(QWidget):
    """
    Wizard Step 8: Full summary of all settings before processing begins.
    """
    start_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings: ClipSettings = None
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
        layout.setSpacing(24)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        title = QLabel("Review Settings")
        title.setObjectName("page_title")
        layout.addWidget(title)

        hint = QLabel("Review your configuration before generating clips.")
        hint.setObjectName("hint_label")
        layout.addWidget(hint)

        # Summary card
        self._summary_card = QFrame()
        self._summary_card.setObjectName("card_elevated")
        self._summary_layout = QVBoxLayout(self._summary_card)
        self._summary_layout.setSpacing(12)
        layout.addWidget(self._summary_card)

        # Disk space warning
        self._disk_warn = QLabel("")
        self._disk_warn.setObjectName("error_label")
        self._disk_warn.setWordWrap(True)
        self._disk_warn.hide()
        layout.addWidget(self._disk_warn)

        layout.addStretch()

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(48, 12, 48, 20)
        btn_back = QPushButton("← Back")
        btn_back.setObjectName("btn_secondary")
        btn_back.clicked.connect(self.back_requested.emit)
        self._btn_start = QPushButton("▶  Start Processing")
        self._btn_start.setObjectName("btn_primary")
        self._btn_start.setMinimumWidth(180)
        self._btn_start.clicked.connect(self.start_requested.emit)
        footer.addWidget(btn_back)
        footer.addStretch()
        footer.addWidget(self._btn_start)
        root.addLayout(footer)

    def load(self, settings: ClipSettings):
        self._settings = settings

        # Clear previous
        while self._summary_layout.count():
            item = self._summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        s = settings
        v = s.source_video

        rows = [
            ("Source Video", v.filename if v else "—"),
            ("Duration", format_seconds_to_hms(v.duration_seconds) if v else "—"),
            ("Resolution", v.resolution_str if v else "—"),
            ("Audio Track", s.selected_audio.display_name if s.selected_audio else "—"),
        ]

        if s.selected_subtitle:
            rows.append(("Subtitle", s.selected_subtitle.display_name))
        else:
            rows.append(("Subtitle", "No subtitles"))

        mode_names = {
            SubtitleMode.NO_SUBTITLES: "None",
            SubtitleMode.EMBEDDED: "Embedded (soft)",
            SubtitleMode.BURNED: "Burned into video",
        }
        rows.append(("Subtitle Output", mode_names.get(s.subtitle_mode, "—")))

        if s.translate_subtitle:
            rows.append(("Translation", f"{s.source_language} → {s.target_language}"))
        else:
            rows.append(("Translation", "None"))

        rows += [
            ("Clip Duration", format_seconds_to_hms(s.clip_duration_seconds)),
            ("Include Partial Clip", "Yes" if s.include_partial_clip else "No"),
            ("Expected Clips", str(s.total_clips)),
            ("Output Folder", s.output_dir or "—"),
            ("Filename Pattern", s.clip_filename(1) + " … " + s.clip_filename(s.total_clips)),
            ("Conflict Handling", s.overwrite_mode.value.replace("_", " ").title()),
        ]

        # Add disk space estimate
        if v and s.total_clips > 0:
            from video_automator.utils.disk_utils import estimate_clipping_space, get_free_disk_space
            est = estimate_clipping_space(
                v.size_bytes, v.duration_seconds, s.clip_duration_seconds, s.total_clips
            )
            free = get_free_disk_space(s.output_dir) if s.output_dir else 0
            rows.append(("Estimated Size", format_size_human(est)))
            rows.append(("Available Space", format_size_human(free)))

            if free > 0 and free < est:
                self._disk_warn.setText(
                    f"⚠  Warning: Available disk space ({format_size_human(free)}) "
                    f"may be insufficient for estimated output ({format_size_human(est)})."
                )
                self._disk_warn.show()
            else:
                self._disk_warn.hide()

        # Render rows
        header_lbl = QLabel("Configuration Summary")
        header_lbl.setObjectName("section_label")
        self._summary_layout.addWidget(header_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        self._summary_layout.addWidget(sep)

        for label, value in rows:
            row_layout = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setObjectName("section_label")
            lbl.setFixedWidth(160)
            val = QLabel(value)
            val.setObjectName("value_label")
            val.setWordWrap(True)
            row_layout.addWidget(lbl)
            row_layout.addWidget(val, 1)
            self._summary_layout.addLayout(row_layout)

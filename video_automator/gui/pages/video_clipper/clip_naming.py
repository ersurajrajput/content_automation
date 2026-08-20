"""Step 7 — Clip Naming Page."""
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QRadioButton, QButtonGroup, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from video_automator.models.clip_settings import ClipSettings, OverwriteMode
from video_automator.utils.file_utils import sanitize_filename, find_existing_conflicts


class ClipNamingPage(QWidget):
    """
    Wizard Step 7: Enter base clip name, see numbering preview, handle existing file conflicts.
    """
    next_requested = Signal(str, object)  # base_name, OverwriteMode
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
        layout.setSpacing(28)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        title = QLabel("Clip Naming")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # ── Name input card ──
        name_card = QFrame()
        name_card.setObjectName("card_elevated")
        name_layout = QVBoxLayout(name_card)
        name_layout.setSpacing(14)

        name_header = QLabel("Base Filename")
        name_header.setObjectName("section_label")
        name_layout.addWidget(name_header)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Podcast_Episode_01")
        self._name_edit.setText("clip")
        self._name_edit.textChanged.connect(self._update_preview)
        name_layout.addWidget(self._name_edit)

        hint = QLabel("Sequential numbering is added automatically: clip_001.mp4, clip_002.mp4 …")
        hint.setObjectName("hint_label")
        hint.setWordWrap(True)
        name_layout.addWidget(hint)

        self._error_name = QLabel("")
        self._error_name.setObjectName("error_label")
        name_layout.addWidget(self._error_name)

        layout.addWidget(name_card)

        # ── Preview card ──
        preview_card = QFrame()
        preview_card.setObjectName("card")
        prev_layout = QVBoxLayout(preview_card)
        prev_layout.setSpacing(10)

        prev_header = QLabel("Filename Preview")
        prev_header.setObjectName("section_label")
        prev_layout.addWidget(prev_header)

        self._preview_list = QListWidget()
        self._preview_list.setMaximumHeight(180)
        self._preview_list.setStyleSheet(
            "QListWidget { font-family: 'Courier New', monospace; font-size: 12px; }"
        )
        prev_layout.addWidget(self._preview_list)

        self._clip_count_lbl = QLabel("")
        self._clip_count_lbl.setObjectName("hint_label")
        prev_layout.addWidget(self._clip_count_lbl)

        layout.addWidget(preview_card)

        # ── Conflict card (hidden initially) ──
        self._conflict_card = QFrame()
        self._conflict_card.setObjectName("card")
        conflict_layout = QVBoxLayout(self._conflict_card)
        conflict_layout.setSpacing(12)

        conflict_hdr = QLabel("⚠  Existing Files Detected")
        conflict_hdr.setStyleSheet("color: #f59e0b; font-weight: 600;")
        conflict_layout.addWidget(conflict_hdr)

        self._conflict_info = QLabel("")
        self._conflict_info.setObjectName("hint_label")
        self._conflict_info.setWordWrap(True)
        conflict_layout.addWidget(self._conflict_info)

        conflict_layout.addWidget(QLabel("How should conflicts be handled?"))
        self._conflict_group = QButtonGroup(self)
        modes = [
            (OverwriteMode.RENUMBER, "Generate new numbering (start after last existing file)"),
            (OverwriteMode.SKIP, "Skip existing files"),
            (OverwriteMode.OVERWRITE, "Overwrite existing files"),
            (OverwriteMode.CANCEL, "Cancel — do not process"),
        ]
        for mode, label in modes:
            radio = QRadioButton(label)
            radio.setStyleSheet("font-size: 12px;")
            self._conflict_group.addButton(radio, list(OverwriteMode).index(mode))
            conflict_layout.addWidget(radio)
        self._conflict_group.button(0).setChecked(True)

        self._conflict_card.hide()
        layout.addWidget(self._conflict_card)
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

    def load(self, settings: ClipSettings):
        self._settings = settings
        self._update_preview()

    def _update_preview(self):
        self._preview_list.clear()
        self._error_name.setText("")
        self._conflict_card.hide()

        raw = self._name_edit.text().strip()
        if not raw:
            self._error_name.setText("Please enter a base filename.")
            self._btn_next.setEnabled(False)
            return

        base = sanitize_filename(raw)
        if base != raw:
            self._error_name.setText(
                f"Some characters were replaced. Effective name: {base}"
            )

        if not self._settings:
            self._btn_next.setEnabled(True)
            return

        total = self._settings.total_clips
        pad = max(3, len(str(total)))

        # Show preview (up to 5 clips + last)
        preview_count = min(5, total)
        for i in range(1, preview_count + 1):
            self._preview_list.addItem(f"  {base}_{str(i).zfill(pad)}.mp4")
        if total > 6:
            self._preview_list.addItem(f"  ...")
        if total > preview_count:
            self._preview_list.addItem(f"  {base}_{str(total).zfill(pad)}.mp4")

        self._clip_count_lbl.setText(f"Total clips: {total}")

        # Check for conflicts
        if self._settings.output_dir and Path(self._settings.output_dir).exists():
            conflicts = find_existing_conflicts(
                self._settings.output_dir, base, total, pad
            )
            if conflicts:
                self._conflict_info.setText(
                    f"{len(conflicts)} file(s) already exist in the output folder "
                    f"(e.g. {conflicts[0]}). Choose how to handle them:"
                )
                self._conflict_card.show()

        self._btn_next.setEnabled(True)

    def _on_next(self):
        base = sanitize_filename(self._name_edit.text().strip())
        if not base:
            return
        bid = self._conflict_group.checkedId()
        mode = list(OverwriteMode)[bid]
        self.next_requested.emit(base, mode)

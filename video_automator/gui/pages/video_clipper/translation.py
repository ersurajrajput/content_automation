"""Step 4 — Subtitle Translation Page."""
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QComboBox, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QThread

from video_automator.models.subtitle_track import SubtitleTrack
from video_automator.services.translation.service import TranslationService
from video_automator.services.translation.base import TranslationNotConfiguredError, TranslationError


SUPPORTED_LANGUAGES = [
    "English", "Hindi", "Spanish", "French", "German",
    "Portuguese", "Bengali", "Tamil", "Telugu", "Marathi",
    "Gujarati", "Japanese", "Chinese", "Arabic", "Russian", "Korean",
]


class TranslationWorker(QThread):
    finished = Signal(str)   # translated subtitle path
    error = Signal(str)

    def __init__(self, subtitle_path: str, source_lang: str, target_lang: str):
        super().__init__()
        self._sub = subtitle_path
        self._src = source_lang
        self._tgt = target_lang

    def run(self):
        try:
            svc = TranslationService()
            out = svc.translate(self._sub, self._src, self._tgt)
            self.finished.emit(out)
        except TranslationNotConfiguredError as e:
            self.error.emit(str(e))
        except TranslationError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")


class TranslationPage(QWidget):
    """
    Wizard Step 4: Optional subtitle translation.
    Shown only when exactly one subtitle track exists.
    """
    next_requested = Signal(bool, str, str, str)
    # (translate: bool, source_lang, target_lang, translated_path_or_empty)
    back_requested = Signal()
    skip_requested = Signal()   # go directly to next without translation

    def __init__(self, parent=None):
        super().__init__(parent)
        self._subtitle_track: Optional[SubtitleTrack] = None
        self._source_video_path = ""
        self._extracted_sub_path = ""
        self._translated_path = ""
        self._worker = None
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

        title = QLabel("Subtitle Options")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # Detected subtitle info card
        self._detect_card = QFrame()
        self._detect_card.setObjectName("info_card")
        detect_layout = QHBoxLayout(self._detect_card)
        detect_layout.setSpacing(16)
        icon = QLabel("💬")
        icon.setStyleSheet("font-size: 28px;")
        detect_layout.addWidget(icon)
        self._detect_lbl = QLabel("Subtitle detected:")
        self._detect_lbl.setStyleSheet("color: #c4b5fd; font-size: 14px;")
        detect_layout.addWidget(self._detect_lbl)
        detect_layout.addStretch()
        layout.addWidget(self._detect_card)

        # Choice
        choice_header = QLabel("Translation")
        choice_header.setObjectName("section_label")
        layout.addWidget(choice_header)

        self._radio_keep = QRadioButton("Keep original subtitle")
        self._radio_keep.setChecked(True)
        self._radio_translate = QRadioButton("Translate subtitle")
        self._radio_group = QButtonGroup(self)
        self._radio_group.addButton(self._radio_keep, 0)
        self._radio_group.addButton(self._radio_translate, 1)
        self._radio_group.buttonClicked.connect(self._on_choice)
        layout.addWidget(self._radio_keep)
        layout.addWidget(self._radio_translate)

        # Translation panel
        self._trans_panel = QFrame()
        self._trans_panel.setObjectName("card")
        trans_layout = QVBoxLayout(self._trans_panel)
        trans_layout.setSpacing(16)

        from_row = QHBoxLayout()
        from_row.addWidget(QLabel("Original language:"))
        self._from_label = QLabel("—")
        self._from_label.setStyleSheet("color: #c4b5fd; font-weight: 600;")
        from_row.addWidget(self._from_label)
        from_row.addStretch()
        trans_layout.addLayout(from_row)

        to_row = QHBoxLayout()
        to_row.addWidget(QLabel("Translate to:"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(SUPPORTED_LANGUAGES)
        self._lang_combo.setCurrentText("Hindi")
        self._lang_combo.setFixedWidth(180)
        to_row.addWidget(self._lang_combo)
        to_row.addStretch()
        trans_layout.addLayout(to_row)

        self._btn_translate = QPushButton("Translate")
        self._btn_translate.setObjectName("btn_secondary")
        self._btn_translate.setFixedWidth(140)
        self._btn_translate.clicked.connect(self._do_translate)
        trans_layout.addWidget(self._btn_translate)

        self._trans_status = QLabel("")
        self._trans_status.setWordWrap(True)
        self._trans_status.setObjectName("hint_label")
        trans_layout.addWidget(self._trans_status)

        self._trans_panel.hide()
        layout.addWidget(self._trans_panel)
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

    def load(self, subtitle_track: Optional[SubtitleTrack], source_video_path: str):
        self._subtitle_track = subtitle_track
        self._source_video_path = source_video_path
        self._translated_path = ""
        self._trans_status.setText("")
        self._radio_keep.setChecked(True)
        self._trans_panel.hide()

        if subtitle_track:
            self._detect_lbl.setText(
                f"Subtitle detected: <b>{subtitle_track.display_name}</b>"
            )
            self._from_label.setText(subtitle_track.language_name or subtitle_track.display_name)
        else:
            self._detect_lbl.setText("No subtitle track selected.")

    def _on_choice(self):
        if self._radio_translate.isChecked():
            self._trans_panel.show()
        else:
            self._trans_panel.hide()
            self._translated_path = ""

    def _do_translate(self):
        if not self._subtitle_track or not self._source_video_path:
            return

        target_lang = self._lang_combo.currentText()
        source_lang = self._subtitle_track.language_name or "English"

        self._trans_status.setText("⏳ Extracting subtitle…")
        self._btn_translate.setEnabled(False)
        self._btn_next.setEnabled(False)

        # Extract subtitle first, then translate
        try:
            import tempfile
            from video_automator.core.video.subtitle_manager import SubtitleManager
            temp_dir = tempfile.mkdtemp(prefix="va_trans_")
            sm = SubtitleManager()
            sub_path = sm.extract_subtitle(
                self._source_video_path, self._subtitle_track, temp_dir, "srt"
            )
            self._extracted_sub_path = sub_path
        except Exception as e:
            self._trans_status.setText(f"⚠  Failed to extract subtitle:\n{e}")
            self._btn_translate.setEnabled(True)
            self._btn_next.setEnabled(True)
            return

        self._trans_status.setText("⏳ Translating…")
        self._worker = TranslationWorker(sub_path, source_lang, target_lang)
        self._worker.finished.connect(self._on_translate_done)
        self._worker.error.connect(self._on_translate_error)
        self._worker.start()

    def _on_translate_done(self, path: str):
        self._translated_path = path
        self._trans_status.setObjectName("success_label")
        self._trans_status.setText(f"✅ Translation complete: {path}")
        self._btn_translate.setEnabled(True)
        self._btn_next.setEnabled(True)

    def _on_translate_error(self, msg: str):
        self._trans_status.setObjectName("error_label")
        self._trans_status.setText(f"⚠  {msg}")
        self._btn_translate.setEnabled(True)
        self._btn_next.setEnabled(True)

    def _on_next(self):
        translate = self._radio_translate.isChecked()
        source_lang = (
            self._subtitle_track.language_name if self._subtitle_track else "English"
        )
        target_lang = self._lang_combo.currentText()
        self.next_requested.emit(translate, source_lang, target_lang, self._translated_path)

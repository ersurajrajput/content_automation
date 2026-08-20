"""Step 6 — Output Location Page."""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from video_automator.config.settings import get_settings
from video_automator.utils.disk_utils import (
    get_free_disk_space, ensure_dir_exists, is_dir_writable
)
from video_automator.utils.time_utils import format_size_human


class OutputSettingsPage(QWidget):
    """
    Wizard Step 6: Choose the output directory for generated clips.
    Validates existence, writability, and optionally creates the folder.
    """
    next_requested = Signal(str)   # selected output directory path
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings()
        self._required_bytes = 0
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

        title = QLabel("Output Location")
        title.setObjectName("page_title")
        layout.addWidget(title)

        hint = QLabel("Choose where to save the generated clips.")
        hint.setObjectName("hint_label")
        layout.addWidget(hint)

        # Path card
        card = QFrame()
        card.setObjectName("card_elevated")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        path_lbl = QLabel("Save clips to:")
        path_lbl.setObjectName("section_label")
        card_layout.addWidget(path_lbl)

        row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select output folder…")
        self._path_edit.setText(self._settings.last_output_dir)
        self._path_edit.textChanged.connect(self._validate)
        row.addWidget(self._path_edit)

        btn_browse = QPushButton("Browse…")
        btn_browse.setObjectName("btn_secondary")
        btn_browse.setFixedWidth(100)
        btn_browse.clicked.connect(self._browse)
        row.addWidget(btn_browse)
        card_layout.addLayout(row)

        # Disk space info
        self._disk_label = QLabel("")
        self._disk_label.setObjectName("hint_label")
        card_layout.addWidget(self._disk_label)

        # Validation messages
        self._error_lbl = QLabel("")
        self._error_lbl.setObjectName("error_label")
        self._error_lbl.setWordWrap(True)
        card_layout.addWidget(self._error_lbl)

        self._ok_lbl = QLabel("")
        self._ok_lbl.setObjectName("success_label")
        card_layout.addWidget(self._ok_lbl)

        layout.addWidget(card)
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

        self._validate()

    def load(self, required_bytes: int = 0):
        """Call before showing this page to set disk space requirement."""
        self._required_bytes = required_bytes
        self._validate()

    def _browse(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder",
            self._path_edit.text() or str(Path.home())
        )
        if folder:
            self._path_edit.setText(folder)

    def _validate(self):
        path = self._path_edit.text().strip()
        self._error_lbl.setText("")
        self._ok_lbl.setText("")
        self._disk_label.setText("")
        self._btn_next.setEnabled(False)

        if not path:
            self._error_lbl.setText("Please select an output folder.")
            return

        p = Path(path)
        if not p.exists():
            self._error_lbl.setText(
                "This folder does not exist. It will be created when you continue."
            )
            self._btn_next.setEnabled(True)
            return

        if not is_dir_writable(path):
            self._error_lbl.setText(
                f"⚠  You don't have write permission to this folder.\n{path}"
            )
            return

        # Disk space
        free = get_free_disk_space(path)
        free_str = format_size_human(free)
        if self._required_bytes > 0:
            req_str = format_size_human(self._required_bytes)
            if free < self._required_bytes:
                self._error_lbl.setText(
                    f"⚠  Insufficient disk space.\n"
                    f"Required: {req_str}  |  Available: {free_str}\n\n"
                    "Please choose a different location."
                )
                return
            self._disk_label.setText(f"Available: {free_str}  |  Required (est.): {req_str}")
        else:
            self._disk_label.setText(f"Available: {free_str}")

        self._ok_lbl.setText(f"✓  Output folder is ready.")
        self._btn_next.setEnabled(True)

    def _on_next(self):
        path = self._path_edit.text().strip()
        p = Path(path)

        if not p.exists():
            reply = QMessageBox.question(
                self,
                "Create Folder?",
                f"The folder does not exist:\n{path}\n\nCreate it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            if not ensure_dir_exists(path):
                self._error_lbl.setText(f"⚠  Failed to create folder: {path}")
                return

        self._settings.last_output_dir = path
        self.next_requested.emit(path)

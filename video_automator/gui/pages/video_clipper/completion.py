"""Step 10 — Completion Page (and Cancellation summary)."""
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from video_automator.core.video.video_processor import ClipResult


class CompletionPage(QWidget):
    """
    Wizard Step 10: Display final results after processing finishes or is cancelled.
    """
    process_another = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_dir = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(24)

        # Header
        self._icon_lbl = QLabel("✅")
        self._icon_lbl.setStyleSheet("font-size: 52px;")
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_lbl)

        self._title_lbl = QLabel("Processing Complete")
        self._title_lbl.setObjectName("page_title")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_lbl)

        # Stats card
        stats_card = QFrame()
        stats_card.setObjectName("card_elevated")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setSpacing(10)

        self._stats_header = QLabel("Results")
        self._stats_header.setObjectName("section_label")
        stats_layout.addWidget(self._stats_header)

        self._clips_lbl = QLabel("")
        self._clips_lbl.setStyleSheet("font-size: 15px; color: #34d399; font-weight: 600;")
        stats_layout.addWidget(self._clips_lbl)

        self._location_lbl = QLabel("")
        self._location_lbl.setObjectName("hint_label")
        self._location_lbl.setWordWrap(True)
        stats_layout.addWidget(self._location_lbl)

        layout.addWidget(stats_card)

        # File list
        file_hdr = QLabel("Generated Files")
        file_hdr.setObjectName("section_label")
        layout.addWidget(file_hdr)

        self._file_list = QListWidget()
        self._file_list.setMaximumHeight(200)
        self._file_list.setStyleSheet(
            "QListWidget { font-family: 'Courier New', monospace; font-size: 11px; }"
        )
        layout.addWidget(self._file_list)

        layout.addStretch()

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._btn_open_folder = QPushButton("📁  Open Folder")
        self._btn_open_folder.setObjectName("btn_secondary")
        self._btn_open_folder.clicked.connect(self._open_folder)

        self._btn_another = QPushButton("Process Another Video")
        self._btn_another.setObjectName("btn_secondary")
        self._btn_another.clicked.connect(self.process_another.emit)

        btn_done = QPushButton("Done")
        btn_done.setObjectName("btn_primary")
        btn_done.setFixedWidth(120)
        btn_done.clicked.connect(self.close_requested.emit)

        btn_row.addWidget(self._btn_open_folder)
        btn_row.addWidget(self._btn_another)
        btn_row.addStretch()
        btn_row.addWidget(btn_done)
        layout.addLayout(btn_row)

    def show_success(self, results: List[ClipResult], output_dir: str, source_name: str):
        self._output_dir = output_dir
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        self._icon_lbl.setText("✅")
        self._title_lbl.setText("Processing Complete!")
        self._title_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #34d399;"
        )

        self._clips_lbl.setText(
            f"{len(successful)} clip(s) generated successfully"
            + (f"  ·  {len(failed)} failed" if failed else "")
        )
        self._location_lbl.setText(f"Saved to: {output_dir}")

        self._file_list.clear()
        for r in successful:
            self._file_list.addItem(f"  ✓  {r.filename}")
        for r in failed:
            self._file_list.addItem(f"  ✗  {r.filename}  (failed)")

    def show_cancelled(self, results: List[ClipResult], output_dir: str, total_expected: int):
        self._output_dir = output_dir
        successful = [r for r in results if r.success]
        remaining = total_expected - len(successful)

        self._icon_lbl.setText("⏹")
        self._title_lbl.setText("Processing Cancelled")
        self._title_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #f59e0b;"
        )

        self._clips_lbl.setText(
            f"{len(successful)} clip(s) saved  ·  {remaining} remaining"
        )
        self._location_lbl.setText(f"Saved to: {output_dir}")

        self._file_list.clear()
        for r in successful:
            self._file_list.addItem(f"  ✓  {r.filename}")

    def _open_folder(self):
        if not self._output_dir:
            return
        if sys.platform == "win32":
            os.startfile(self._output_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self._output_dir])
        else:
            subprocess.Popen(["xdg-open", self._output_dir])

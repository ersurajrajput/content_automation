"""Clips Gallery Page — folder-based browser of previously clipped videos."""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QSizePolicy, QGridLayout,
    QSplitter, QListWidget, QListWidgetItem, QStackedWidget,
    QToolButton, QSpacerItem, QMessageBox,
)
from PySide6.QtCore import (
    Qt, Signal, QSize, QThreadPool, QTimer, QMimeData,
)
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QBrush, QFont

from video_automator.config.settings import get_settings
from video_automator.gui.pages.gallery.thumbnail_worker import ThumbnailTask

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def _get_video_files(folder: str) -> List[str]:
    """Return sorted list of video file paths in a folder (non-recursive)."""
    try:
        p = Path(folder)
        if not p.is_dir():
            return []
        return sorted(
            [str(f) for f in p.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS],
            key=lambda x: Path(x).name.lower(),
        )
    except Exception:
        return []


def _file_size_str(path: str) -> str:
    try:
        b = os.path.getsize(path)
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.0f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"
    except Exception:
        return "—"


def _duration_from_ffprobe(path: str) -> str:
    """Quick ffprobe call to get duration string."""
    try:
        result = subprocess.run(
            [
                shutil.which("ffprobe") or "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                path,
            ],
            capture_output=True, text=True, timeout=8,
        )
        secs = float(result.stdout.strip())
        h, rem = divmod(int(secs), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# Video Card Widget
# ─────────────────────────────────────────────────────────────────────────────

class VideoCard(QWidget):
    """Thumbnail card for a single video clip."""
    play_requested = Signal(str)
    open_folder_requested = Signal(str)

    CARD_W = 220
    CARD_H = 260

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self._path = video_path
        self._name = Path(video_path).name
        self._folder = str(Path(video_path).parent)
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Card frame
        frame = QFrame()
        frame.setObjectName("video_card")
        frame.setStyleSheet("""
            QFrame#video_card {
                background-color: #1a1a27;
                border: 1px solid #252535;
                border-radius: 12px;
            }
            QFrame#video_card:hover {
                border-color: #7c3aed;
                background-color: #1e1030;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 10)
        frame_layout.setSpacing(6)

        # Thumbnail area
        self._thumb_lbl = QLabel()
        self._thumb_lbl.setFixedSize(self.CARD_W - 2, 126)
        self._thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_lbl.setStyleSheet(
            "background-color: #12121c; border-radius: 12px 12px 0 0;"
        )
        self._set_placeholder_thumb()
        frame_layout.addWidget(self._thumb_lbl)

        # Filename
        name_lbl = QLabel(self._name)
        name_lbl.setWordWrap(True)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            "color: #d1d5db; font-size: 11px; font-weight: 600; padding: 0 8px;"
        )
        name_lbl.setMaximumHeight(40)
        frame_layout.addWidget(name_lbl)

        # Size label (lazy — filled later)
        self._size_lbl = QLabel(_file_size_str(self._path))
        self._size_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._size_lbl.setStyleSheet("color: #6b7280; font-size: 10px;")
        frame_layout.addWidget(self._size_lbl)

        # Duration label (filled async)
        self._dur_lbl = QLabel("—")
        self._dur_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dur_lbl.setStyleSheet("color: #a78bfa; font-size: 10px; font-weight: 600;")
        frame_layout.addWidget(self._dur_lbl)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 0, 8, 0)
        btn_row.setSpacing(6)

        btn_play = QPushButton("▶")
        btn_play.setToolTip("Play this clip")
        btn_play.setFixedSize(36, 28)
        btn_play.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed; color: white;
                border: none; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #8b5cf6; }
        """)
        btn_play.clicked.connect(lambda: self.play_requested.emit(self._path))

        btn_folder = QPushButton("📁")
        btn_folder.setToolTip("Open containing folder")
        btn_folder.setFixedSize(36, 28)
        btn_folder.setStyleSheet("""
            QPushButton {
                background-color: #252535; color: #9ca3af;
                border: 1px solid #2d2d45; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #2d2d45; }
        """)
        btn_folder.clicked.connect(lambda: self.open_folder_requested.emit(self._folder))

        btn_row.addStretch()
        btn_row.addWidget(btn_play)
        btn_row.addWidget(btn_folder)
        btn_row.addStretch()
        frame_layout.addLayout(btn_row)

        layout.addWidget(frame)

    def _set_placeholder_thumb(self):
        pix = QPixmap(self.CARD_W - 2, 126)
        pix.fill(QColor("#12121c"))
        painter = QPainter(pix)
        painter.setPen(QColor("#374151"))
        font = QFont()
        font.setPixelSize(28)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "🎬")
        painter.end()
        self._thumb_lbl.setPixmap(pix)

    def set_thumbnail(self, thumb_path: str):
        pix = QPixmap(thumb_path)
        if not pix.isNull():
            pix = pix.scaled(
                self.CARD_W - 2, 126,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Centre-crop
            if pix.width() > self.CARD_W - 2:
                x = (pix.width() - (self.CARD_W - 2)) // 2
                pix = pix.copy(x, 0, self.CARD_W - 2, 126)
            self._thumb_lbl.setPixmap(pix)

    def set_duration(self, dur: str):
        self._dur_lbl.setText(dur)

    def mouseDoubleClickEvent(self, event):
        self.play_requested.emit(self._path)


# ─────────────────────────────────────────────────────────────────────────────
# Folder Panel (left sidebar list)
# ─────────────────────────────────────────────────────────────────────────────

class FolderPanel(QWidget):
    folder_selected = Signal(str)
    folder_removed = Signal(str)
    add_folder_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setObjectName("folder_panel")
        self.setStyleSheet("""
            QWidget#folder_panel {
                background-color: #14141c;
                border-right: 1px solid #1e1e2e;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet("background-color: #14141c;")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(14, 14, 8, 10)
        lbl = QLabel("Folders")
        lbl.setStyleSheet(
            "color: #a78bfa; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;"
        )
        hdr_layout.addWidget(lbl)
        hdr_layout.addStretch()

        btn_add = QPushButton("+")
        btn_add.setToolTip("Add output folder to gallery")
        btn_add.setFixedSize(26, 26)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95; color: #c4b5fd;
                border: none; border-radius: 5px; font-size: 16px; font-weight: 700;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        btn_add.clicked.connect(self.add_folder_clicked.emit)
        hdr_layout.addWidget(btn_add)
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e1e2e; max-height: 1px;")
        layout.addWidget(sep)

        # List
        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget {
                background-color: #14141c;
                border: none;
                color: #9ca3af;
                font-size: 12px;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 8px 10px;
                margin: 2px 4px;
            }
            QListWidget::item:hover { background-color: #1e1e2e; color: #e8e8f0; }
            QListWidget::item:selected {
                background-color: #2d1a4e;
                color: #c4b5fd;
                border: 1px solid #4c1d95;
            }
        """)
        self._list.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(self._list, 1)

        # Remove button
        btn_remove = QPushButton("Remove Folder")
        btn_remove.setStyleSheet("""
            QPushButton {
                background: transparent; color: #4b5563;
                border: none; font-size: 11px; padding: 8px;
            }
            QPushButton:hover { color: #f87171; }
        """)
        btn_remove.clicked.connect(self._remove_current)
        layout.addWidget(btn_remove)

    def load_folders(self, folders: List[str]):
        self._list.clear()
        for f in folders:
            p = Path(f)
            item = QListWidgetItem(f"📁  {p.name}")
            item.setToolTip(str(p))
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def add_folder(self, folder: str):
        p = Path(folder)
        # Check if already present
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == str(p):
                self._list.setCurrentRow(i)
                return
        item = QListWidgetItem(f"📁  {p.name}")
        item.setToolTip(str(p))
        item.setData(Qt.ItemDataRole.UserRole, str(p))
        self._list.addItem(item)
        self._list.setCurrentItem(item)

    def _on_item_changed(self, current, previous):
        if current:
            self.folder_selected.emit(current.data(Qt.ItemDataRole.UserRole))

    def _remove_current(self):
        item = self._list.currentItem()
        if item:
            folder = item.data(Qt.ItemDataRole.UserRole)
            self._list.takeItem(self._list.row(item))
            self.folder_removed.emit(folder)

    def all_folders(self) -> List[str]:
        return [
            self._list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._list.count())
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Video Grid Panel (right side)
# ─────────────────────────────────────────────────────────────────────────────

class VideoGridPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(4)
        self._cards: Dict[str, VideoCard] = {}
        self._dur_cache: Dict[str, str] = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0f0f13; border-bottom: 1px solid #1e1e2e;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 10, 20, 10)

        self._folder_lbl = QLabel("Select a folder")
        self._folder_lbl.setStyleSheet("color: #6b7280; font-size: 12px;")
        tb_layout.addWidget(self._folder_lbl)
        tb_layout.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: #4b5563; font-size: 11px;")
        tb_layout.addWidget(self._count_lbl)

        self._btn_refresh = QPushButton("⟳ Refresh")
        self._btn_refresh.setStyleSheet("""
            QPushButton {
                background: transparent; color: #6b7280; border: none;
                font-size: 12px; padding: 4px 8px;
            }
            QPushButton:hover { color: #a78bfa; }
        """)
        self._btn_refresh.clicked.connect(self._refresh_current)
        tb_layout.addWidget(self._btn_refresh)
        root.addWidget(toolbar)

        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0f0f13; }")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background-color: #0f0f13;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(24, 24, 24, 24)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_container)
        root.addWidget(scroll, 1)

        # Empty state
        self._empty_widget = QWidget()
        empty_layout = QVBoxLayout(self._empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_icon = QLabel("🎬")
        self._empty_icon.setStyleSheet("font-size: 52px;")
        self._empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_msg = QLabel("No clips found in this folder.")
        self._empty_msg.setStyleSheet("color: #374151; font-size: 14px;")
        self._empty_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self._empty_icon)
        empty_layout.addWidget(self._empty_msg)
        self._empty_widget.hide()
        root.addWidget(self._empty_widget)

        self._current_folder = ""

    def load_folder(self, folder: str):
        self._current_folder = folder
        p = Path(folder)
        self._folder_lbl.setText(str(p))

        # Clear existing cards
        self._cards.clear()
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        files = _get_video_files(folder)
        self._count_lbl.setText(f"{len(files)} clip(s)" if files else "")

        if not files:
            self._empty_msg.setText(
                f"No video clips found in:\n{folder}"
                if p.exists() else
                f"Folder not found:\n{folder}"
            )
            self._empty_widget.show()
            self._grid_container.hide()
            return

        self._empty_widget.hide()
        self._grid_container.show()

        # Lay out cards in a grid (auto columns based on width ~220px each)
        cols = max(1, (self._grid_container.width() - 48) // (VideoCard.CARD_W + 16))
        cols = max(cols, 3)  # minimum 3 columns

        for idx, video_path in enumerate(files):
            card = VideoCard(video_path)
            card.play_requested.connect(self._play_video)
            card.open_folder_requested.connect(self._open_folder)
            self._cards[video_path] = card
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(card, row, col)

            # Queue thumbnail + duration generation
            self._queue_thumbnail(video_path)
            self._queue_duration(video_path, card)

    def _queue_thumbnail(self, video_path: str):
        task = ThumbnailTask(video_path)
        task.signals.done.connect(self._on_thumb_ready)
        self._pool.start(task)

    def _on_thumb_ready(self, video_path: str, thumb_path: str):
        card = self._cards.get(video_path)
        if card:
            card.set_thumbnail(thumb_path)

    def _queue_duration(self, video_path: str, card: VideoCard):
        if video_path in self._dur_cache:
            card.set_duration(self._dur_cache[video_path])
            return

        class DurWorker(QThreadPool):
            pass

        from PySide6.QtCore import QRunnable
        parent = self

        class DurTask(QRunnable):
            def __init__(self):
                super().__init__()
                self.setAutoDelete(True)

            def run(self):
                dur = _duration_from_ffprobe(video_path)
                parent._dur_cache[video_path] = dur
                c = parent._cards.get(video_path)
                if c:
                    # Safe cross-thread UI update via QTimer
                    QTimer.singleShot(0, lambda: c.set_duration(dur))

        self._pool.start(DurTask())

    def _refresh_current(self):
        if self._current_folder:
            self.load_folder(self._current_folder)

    def _play_video(self, path: str):
        if not Path(path).exists():
            QMessageBox.warning(None, "File Not Found", f"File does not exist:\n{path}")
            return
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                # Try common Linux video players, fallback to xdg-open
                for player in ("mpv", "vlc", "ffplay", "totem"):
                    if shutil.which(player):
                        args = [player]
                        if player == "ffplay":
                            args += ["-autoexit"]
                        args.append(path)
                        subprocess.Popen(args)
                        return
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(None, "Playback Error", str(e))

    def _open_folder(self, folder: str):
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Gallery Page (main)
# ─────────────────────────────────────────────────────────────────────────────

class GalleryPage(QWidget):
    """
    Clips Gallery — shows previously generated clips organised by output folder.
    Folders are remembered across sessions via AppSettings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings()
        self._build_ui()
        self._load_saved_folders()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Page header ──
        header = QWidget()
        header.setStyleSheet(
            "background-color: #0f0f13; border-bottom: 1px solid #1e1e2e;"
        )
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(32, 20, 32, 20)

        title = QLabel("Clips Gallery")
        title.setObjectName("page_title")
        hdr_layout.addWidget(title)
        hdr_layout.addStretch()

        subtitle = QLabel("Browse previously generated clips by folder.")
        subtitle.setObjectName("hint_label")
        hdr_layout.addWidget(subtitle)

        btn_add = QPushButton("+ Add Folder")
        btn_add.setObjectName("btn_secondary")
        btn_add.setFixedWidth(120)
        btn_add.clicked.connect(self._browse_add_folder)
        hdr_layout.addSpacing(16)
        hdr_layout.addWidget(btn_add)
        root.addWidget(header)

        # ── Splitter: [Folder list | Video grid] ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle { background-color: #1e1e2e; }
        """)

        self._folder_panel = FolderPanel()
        self._folder_panel.folder_selected.connect(self._on_folder_selected)
        self._folder_panel.folder_removed.connect(self._on_folder_removed)
        self._folder_panel.add_folder_clicked.connect(self._browse_add_folder)
        splitter.addWidget(self._folder_panel)

        self._grid_panel = VideoGridPanel()
        splitter.addWidget(self._grid_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 1)

    def _load_saved_folders(self):
        folders = self._settings.get("gallery_folders", [])
        # Always include the last used output dir if it has videos
        last = self._settings.last_output_dir
        if last and Path(last).exists() and last not in folders:
            if _get_video_files(last):
                folders = [last] + folders
        self._folder_panel.load_folders(folders)

    def _save_folders(self):
        self._settings.set("gallery_folders", self._folder_panel.all_folders())

    def _browse_add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Clips Folder",
            self._settings.last_output_dir,
        )
        if folder:
            self._folder_panel.add_folder(folder)
            self._save_folders()

    def _on_folder_selected(self, folder: str):
        self._grid_panel.load_folder(folder)

    def _on_folder_removed(self, folder: str):
        self._save_folders()

    def refresh(self):
        """Call this when returning to the gallery after a clipping job finishes."""
        last = self._settings.last_output_dir
        if last and Path(last).exists():
            self._folder_panel.add_folder(last)
            self._save_folders()
            self._grid_panel.load_folder(last)

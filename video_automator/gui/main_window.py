"""Main application window — wizard orchestrator + gallery."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from video_automator.models.clip_settings import ClipSettings, SubtitleMode
from video_automator.gui.widgets.wizard_header import WizardHeader
from video_automator.gui.pages.video_clipper.video_selection import VideoSelectionPage
from video_automator.gui.pages.video_clipper.audio_selection import AudioSelectionPage
from video_automator.gui.pages.video_clipper.subtitle_selection import SubtitleSelectionPage
from video_automator.gui.pages.video_clipper.translation import TranslationPage
from video_automator.gui.pages.video_clipper.clip_settings import ClipSettingsPage
from video_automator.gui.pages.video_clipper.output_settings import OutputSettingsPage
from video_automator.gui.pages.video_clipper.clip_naming import ClipNamingPage
from video_automator.gui.pages.video_clipper.review import ReviewPage
from video_automator.gui.pages.video_clipper.processing import ProcessingPage
from video_automator.gui.pages.video_clipper.completion import CompletionPage
from video_automator.gui.pages.gallery.gallery_page import GalleryPage


# ── Page indices inside the wizard QStackedWidget ────────────────────────────
PAGE_VIDEO = 0
PAGE_AUDIO = 1
PAGE_SUBTITLE = 2
PAGE_TRANSLATION = 3
PAGE_CLIP_SETTINGS = 4
PAGE_OUTPUT = 5
PAGE_NAMING = 6
PAGE_REVIEW = 7
PAGE_PROCESSING = 8
PAGE_COMPLETION = 9

# ── Top-level view indices inside the root QStackedWidget ────────────────────
VIEW_CLIPPER = 0
VIEW_GALLERY = 1


class MainWindow(QMainWindow):
    """
    Primary application window containing:
    - Left sidebar with clickable nav items
    - Top-level QStackedWidget  (Clipper wizard  |  Gallery)
    - Wizard step-indicator header (hidden on Gallery view)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Automator — Clip Generator")
        self.setMinimumSize(QSize(980, 700))
        self.resize(1140, 780)

        self._clip_settings = ClipSettings()
        self._audio_tracks = []
        self._subtitle_tracks = []
        self._active_nav = None  # currently highlighted sidebar item

        self._build_ui()
        self._connect_pages()

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        app_title = QLabel("Video\nAutomator")
        app_title.setObjectName("app_title")
        sidebar_layout.addWidget(app_title)

        app_sub = QLabel("CLIP GENERATOR")
        app_sub.setObjectName("app_subtitle")
        sidebar_layout.addWidget(app_sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e1e2e; max-height: 1px;")
        sidebar_layout.addWidget(sep)

        # Nav items — (icon, label, view_index_or_None_for_disabled)
        nav_items = [
            ("🎬", "Video Clipper", VIEW_CLIPPER),
            ("🖼", "Clips Gallery",  VIEW_GALLERY),
            ("📤", "YouTube",        None),
            ("📘", "Facebook",       None),
            ("🎵", "TikTok",         None),
            ("📅", "Scheduler",      None),
            ("⚙",  "Settings",       None),
        ]

        self._nav_widgets = {}  # label -> (widget, lbl, view_idx)
        for icon, label, view_idx in nav_items:
            item_w = QWidget()
            item_w.setFixedHeight(44)
            item_layout = QHBoxLayout(item_w)
            item_layout.setContentsMargins(16, 0, 16, 0)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 16px; min-width: 22px;")
            lbl = QLabel(label)

            if view_idx is not None:
                # Clickable
                lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
                item_w.setCursor(Qt.CursorShape.PointingHandCursor)
                item_w.mousePressEvent = lambda e, vi=view_idx, lbl_=label: self._switch_view(vi, lbl_)
            else:
                lbl.setStyleSheet("color: #374151; font-size: 13px;")

            item_layout.addWidget(icon_lbl)
            item_layout.addWidget(lbl)
            item_layout.addStretch()
            sidebar_layout.addWidget(item_w)
            self._nav_widgets[label] = (item_w, lbl, view_idx)

        sidebar_layout.addStretch()

        ver = QLabel("v1.0.0  ·  Video Module")
        ver.setStyleSheet("color: #374151; font-size: 10px; padding: 12px 16px;")
        sidebar_layout.addWidget(ver)

        root.addWidget(sidebar)

        # ── Right side ────────────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Wizard step indicator (shown only for clipper)
        self._wizard_header = WizardHeader()
        right_layout.addWidget(self._wizard_header)

        # Root-level stack: [Clipper wizard | Gallery]
        self._root_stack = QStackedWidget()
        right_layout.addWidget(self._root_stack)

        # ── Clipper Wizard ────────────────────────────────────────────────────
        clipper_container = QWidget()
        clipper_layout = QVBoxLayout(clipper_container)
        clipper_layout.setContentsMargins(0, 0, 0, 0)
        clipper_layout.setSpacing(0)

        self._stack = QStackedWidget()
        clipper_layout.addWidget(self._stack)

        self._pg_video      = VideoSelectionPage()
        self._pg_audio      = AudioSelectionPage()
        self._pg_subtitle   = SubtitleSelectionPage()
        self._pg_translation = TranslationPage()
        self._pg_clip       = ClipSettingsPage()
        self._pg_output     = OutputSettingsPage()
        self._pg_naming     = ClipNamingPage()
        self._pg_review     = ReviewPage()
        self._pg_processing = ProcessingPage()
        self._pg_completion = CompletionPage()

        for page in [
            self._pg_video, self._pg_audio, self._pg_subtitle,
            self._pg_translation, self._pg_clip, self._pg_output,
            self._pg_naming, self._pg_review, self._pg_processing,
            self._pg_completion,
        ]:
            self._stack.addWidget(page)

        self._root_stack.addWidget(clipper_container)   # VIEW_CLIPPER = 0

        # ── Gallery ───────────────────────────────────────────────────────────
        self._pg_gallery = GalleryPage()
        self._root_stack.addWidget(self._pg_gallery)    # VIEW_GALLERY = 1

        root.addWidget(right, 1)

        # Activate default view
        self._switch_view(VIEW_CLIPPER, "Video Clipper")

    # ─────────────────────────────────────────────────────────────────────────
    # Sidebar navigation
    # ─────────────────────────────────────────────────────────────────────────

    def _switch_view(self, view_idx: int, label: str):
        self._root_stack.setCurrentIndex(view_idx)

        # Show wizard header only for clipper
        self._wizard_header.setVisible(view_idx == VIEW_CLIPPER)

        # Refresh gallery when switching to it
        if view_idx == VIEW_GALLERY:
            self._pg_gallery.refresh()

        # Update sidebar highlight
        for lbl_key, (item_w, lbl_widget, vi) in self._nav_widgets.items():
            if vi is not None:
                if lbl_key == label:
                    lbl_widget.setStyleSheet(
                        "color: #c4b5fd; font-size: 13px; font-weight: 600;"
                    )
                    item_w.setStyleSheet(
                        "background-color: #1e1030; border-right: 3px solid #7c3aed;"
                    )
                else:
                    lbl_widget.setStyleSheet("color: #9ca3af; font-size: 13px;")
                    item_w.setStyleSheet("")

    # ─────────────────────────────────────────────────────────────────────────
    # Page wiring
    # ─────────────────────────────────────────────────────────────────────────

    def _connect_pages(self):
        self._pg_video.next_requested.connect(self._on_video_selected)
        self._pg_audio.next_requested.connect(self._on_audio_selected)
        self._pg_audio.back_requested.connect(lambda: self._goto(PAGE_VIDEO))
        self._pg_subtitle.next_requested.connect(self._on_subtitle_selected)
        self._pg_subtitle.back_requested.connect(lambda: self._goto(PAGE_AUDIO))
        self._pg_translation.next_requested.connect(self._on_translation_done)
        self._pg_translation.back_requested.connect(lambda: self._goto(PAGE_SUBTITLE))
        self._pg_clip.next_requested.connect(self._on_clip_settings_done)
        self._pg_clip.back_requested.connect(self._clip_settings_back)
        self._pg_output.next_requested.connect(self._on_output_selected)
        self._pg_output.back_requested.connect(lambda: self._goto(PAGE_CLIP_SETTINGS))
        self._pg_naming.next_requested.connect(self._on_naming_done)
        self._pg_naming.back_requested.connect(lambda: self._goto(PAGE_OUTPUT))
        self._pg_review.start_requested.connect(self._on_start_processing)
        self._pg_review.back_requested.connect(lambda: self._goto(PAGE_NAMING))
        self._pg_processing.finished.connect(self._on_processing_done)
        self._pg_processing.cancelled.connect(self._on_processing_cancelled)
        self._pg_completion.process_another.connect(self._restart)
        self._pg_completion.close_requested.connect(self.close)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _goto(self, page_idx: int):
        self._stack.setCurrentIndex(page_idx)
        self._wizard_header.set_step(page_idx)

    def _restart(self):
        self._clip_settings = ClipSettings()
        self._audio_tracks = []
        self._subtitle_tracks = []
        self._goto(PAGE_VIDEO)

    # ─────────────────────────────────────────────────────────────────────────
    # Page transitions
    # ─────────────────────────────────────────────────────────────────────────

    def _on_video_selected(self, video_info, audio_tracks, subtitle_tracks):
        self._clip_settings.source_video = video_info
        self._audio_tracks = audio_tracks
        self._subtitle_tracks = subtitle_tracks
        self._pg_audio.load_tracks(audio_tracks, video_path=video_info.path)
        self._goto(PAGE_AUDIO)

    def _on_audio_selected(self, audio_track):
        self._clip_settings.selected_audio = audio_track
        self._pg_subtitle.load_tracks(self._subtitle_tracks)
        self._goto(PAGE_SUBTITLE)

    def _on_subtitle_selected(self, subtitle_track):
        self._clip_settings.selected_subtitle = subtitle_track
        if len(self._subtitle_tracks) == 1 and subtitle_track is not None:
            self._pg_translation.load(subtitle_track, self._clip_settings.source_video.path)
            self._goto(PAGE_TRANSLATION)
        else:
            self._pg_clip.load(
                self._clip_settings.source_video.duration_seconds,
                subtitle_track is not None,
            )
            self._goto(PAGE_CLIP_SETTINGS)

    def _on_translation_done(self, translate, src_lang, tgt_lang, translated_path):
        self._clip_settings.translate_subtitle = translate
        self._clip_settings.source_language = src_lang
        self._clip_settings.target_language = tgt_lang
        self._clip_settings.translated_subtitle_path = translated_path or None
        self._pg_clip.load(
            self._clip_settings.source_video.duration_seconds,
            self._clip_settings.selected_subtitle is not None,
        )
        self._goto(PAGE_CLIP_SETTINGS)

    def _clip_settings_back(self):
        if len(self._subtitle_tracks) == 1 and self._clip_settings.selected_subtitle:
            self._goto(PAGE_TRANSLATION)
        else:
            self._goto(PAGE_SUBTITLE)

    def _on_clip_settings_done(self, duration, include_partial, subtitle_mode):
        self._clip_settings.clip_duration_seconds = duration
        self._clip_settings.include_partial_clip = include_partial
        self._clip_settings.subtitle_mode = subtitle_mode
        v = self._clip_settings.source_video
        from video_automator.utils.disk_utils import estimate_clipping_space
        req = estimate_clipping_space(
            v.size_bytes, v.duration_seconds, duration, self._clip_settings.total_clips
        ) if v else 0
        self._pg_output.load(req)
        self._goto(PAGE_OUTPUT)

    def _on_output_selected(self, output_dir):
        self._clip_settings.output_dir = output_dir
        self._pg_naming.load(self._clip_settings)
        self._goto(PAGE_NAMING)

    def _on_naming_done(self, base_name, overwrite_mode):
        self._clip_settings.base_name = base_name
        self._clip_settings.overwrite_mode = overwrite_mode
        self._pg_review.load(self._clip_settings)
        self._goto(PAGE_REVIEW)

    def _on_start_processing(self):
        self._goto(PAGE_PROCESSING)
        self._pg_processing.start(self._clip_settings)

    def _on_processing_done(self, results):
        self._pg_completion.show_success(
            results,
            self._clip_settings.output_dir,
            self._clip_settings.source_video.filename if self._clip_settings.source_video else "",
        )
        self._goto(PAGE_COMPLETION)
        # Auto-refresh gallery folder list
        self._pg_gallery.refresh()

    def _on_processing_cancelled(self, results):
        self._pg_completion.show_cancelled(
            results,
            self._clip_settings.output_dir,
            self._clip_settings.total_clips,
        )
        self._goto(PAGE_COMPLETION)
        self._pg_gallery.refresh()

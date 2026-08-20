"""Background video clip processor using QThread."""
import os
import time
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Signal, QObject

from video_automator.models.clip_settings import ClipSettings, SubtitleMode
from video_automator.core.video.ffmpeg_manager import get_ffmpeg_manager
from video_automator.core.video.subtitle_manager import SubtitleManager
from video_automator.utils.time_utils import format_seconds_to_timecode, format_seconds_to_hms
from video_automator.utils.file_utils import create_temp_dir, cleanup_temp_dir


class ClipResult:
    """Result of a single clip generation."""
    def __init__(self, index: int, filename: str, path: str, success: bool, error: str = ""):
        self.index = index
        self.filename = filename
        self.path = path
        self.success = success
        self.error = error


class VideoProcessor(QThread):
    """
    Background QThread that generates clips from a source video using FFmpeg.

    Signals:
        progress_changed(int, int): (completed_clips, total_clips)
        clip_started(int, str, float, float): (clip_num, filename, start_sec, end_sec)
        clip_finished(int, str, bool): (clip_num, filename, success)
        status_message(str): Human-readable status update
        error_occurred(str): Error message
        finished_processing(list): List[ClipResult] when done
        speed_updated(str): Processing speed / ETA string
    """
    progress_changed = Signal(int, int)
    clip_started = Signal(int, str, float, float)
    clip_finished = Signal(int, str, bool)
    status_message = Signal(str)
    error_occurred = Signal(str)
    finished_processing = Signal(list)
    speed_updated = Signal(str)

    def __init__(self, settings: ClipSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._cancelled = False
        self._current_proc = None
        self._results: List[ClipResult] = []

    def cancel(self):
        """Request cancellation. Kills current FFmpeg process."""
        self._cancelled = True
        if self._current_proc:
            try:
                self._current_proc.kill()
            except Exception:
                pass

    def run(self):
        """Main processing loop — runs in background thread."""
        settings = self._settings
        video = settings.source_video
        temp_dir = create_temp_dir()

        try:
            total = settings.total_clips
            if total <= 0:
                self.error_occurred.emit("No clips to generate. Check clip duration settings.")
                return

            self.status_message.emit("Preparing subtitle tracks…")
            subtitle_path = self._prepare_subtitle(video.path, temp_dir)

            pad = settings.pad_width
            start_offset = self._resolve_start_index(settings)
            completed = 0
            start_time = time.time()

            for i in range(total):
                if self._cancelled:
                    break

                clip_num = start_offset + i
                filename = settings.clip_filename(clip_num)
                output_path = str(Path(settings.output_dir) / filename)

                clip_start = i * settings.clip_duration_seconds
                clip_end = min(
                    clip_start + settings.clip_duration_seconds,
                    video.duration_seconds,
                )
                duration = clip_end - clip_start

                self.clip_started.emit(clip_num, filename, clip_start, clip_end)
                self.status_message.emit(
                    f"Generating clip {clip_num}: {format_seconds_to_hms(clip_start)} → "
                    f"{format_seconds_to_hms(clip_end)}"
                )

                # Handle skip / overwrite
                if Path(output_path).exists():
                    from video_automator.models.clip_settings import OverwriteMode
                    if settings.overwrite_mode == OverwriteMode.SKIP:
                        self._results.append(ClipResult(clip_num, filename, output_path, True))
                        completed += 1
                        self.clip_finished.emit(clip_num, filename, True)
                        self.progress_changed.emit(completed, total)
                        continue
                    elif settings.overwrite_mode == OverwriteMode.OVERWRITE:
                        try:
                            os.remove(output_path)
                        except Exception:
                            pass

                success = self._generate_clip(
                    video.path,
                    output_path,
                    clip_start,
                    duration,
                    subtitle_path,
                )

                result = ClipResult(clip_num, filename, output_path, success)
                self._results.append(result)

                if not self._cancelled:
                    completed += 1
                    self.clip_finished.emit(clip_num, filename, success)
                    self.progress_changed.emit(completed, total)

                    # ETA
                    elapsed = time.time() - start_time
                    if completed > 0:
                        rate = elapsed / completed
                        remaining = rate * (total - completed)
                        self.speed_updated.emit(
                            f"ETA: {format_seconds_to_hms(remaining)}  |  "
                            f"{rate:.1f}s/clip"
                        )

        except Exception as e:
            self.error_occurred.emit(
                f"Processing failed unexpectedly.\n\nReason:\n{str(e)}"
            )
        finally:
            cleanup_temp_dir(temp_dir)
            self.finished_processing.emit(self._results)

    def _resolve_start_index(self, settings: ClipSettings) -> int:
        """Determine the starting clip number (e.g. for renumber mode)."""
        from video_automator.models.clip_settings import OverwriteMode
        from video_automator.utils.file_utils import find_next_free_index
        if settings.overwrite_mode == OverwriteMode.RENUMBER:
            return find_next_free_index(
                settings.output_dir, settings.base_name, settings.pad_width
            )
        return 1

    def _prepare_subtitle(self, video_path: str, temp_dir: str) -> Optional[str]:
        """Extract and optionally translate subtitle. Returns path or None."""
        settings = self._settings
        if settings.subtitle_mode == SubtitleMode.NO_SUBTITLES:
            return None
        if not settings.selected_subtitle:
            return None

        sm = SubtitleManager()
        fmt = "ass" if settings.subtitle_mode == SubtitleMode.BURNED else "srt"

        if settings.subtitle_mode == SubtitleMode.BURNED:
            sub_path = sm.extract_subtitle_for_burning(
                video_path, settings.selected_subtitle, temp_dir
            )
        else:
            sub_path = sm.extract_subtitle(
                video_path, settings.selected_subtitle, temp_dir, fmt
            )

        # Translation
        if settings.translate_subtitle and settings.translated_subtitle_path:
            return settings.translated_subtitle_path

        return sub_path

    def _generate_clip(
        self,
        video_path: str,
        output_path: str,
        start_sec: float,
        duration_sec: float,
        subtitle_path: Optional[str],
    ) -> bool:
        """Build and run the FFmpeg command for a single clip. Returns True on success."""
        settings = self._settings
        mgr = get_ffmpeg_manager()

        audio_idx = settings.selected_audio.index if settings.selected_audio else 0

        # Base args: fast seek before input for accuracy
        cmd = [
            "-ss", format_seconds_to_timecode(start_sec),
            "-i", video_path,
            "-t", format_seconds_to_timecode(duration_sec),
        ]

        # Map video and selected audio
        cmd += [
            "-map", "0:v:0",
            "-map", f"0:a:{audio_idx}",
        ]

        if settings.subtitle_mode == SubtitleMode.BURNED and subtitle_path:
            burn_filter = SubtitleManager.build_burn_filter(subtitle_path)
            cmd += [
                "-vf", burn_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
            ]
        elif settings.subtitle_mode == SubtitleMode.EMBEDDED and subtitle_path:
            cmd += [
                "-map", f"0:s:{settings.selected_subtitle.index}",
                "-c:v", "copy",
                "-c:a", "copy",
                "-c:s", "mov_text",
            ]
        else:
            # Fast stream copy — no re-encode
            cmd += [
                "-c:v", "copy",
                "-c:a", "copy",
            ]

        # Avoid negative timestamps
        cmd += [
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            output_path,
        ]

        try:
            proc = mgr.start_ffmpeg(cmd)
            self._current_proc = proc

            while True:
                line = proc.stderr.readline()
                if not line and proc.poll() is not None:
                    break
                if self._cancelled:
                    proc.kill()
                    return False

            proc.wait()
            self._current_proc = None
            return proc.returncode == 0

        except Exception as e:
            self.error_occurred.emit(f"FFmpeg error on clip: {e}")
            return False

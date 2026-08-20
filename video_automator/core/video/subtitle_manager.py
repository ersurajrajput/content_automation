"""Subtitle extraction and preparation for FFmpeg processing."""
import os
import subprocess
from pathlib import Path
from typing import Optional

from video_automator.models.subtitle_track import SubtitleTrack
from video_automator.core.video.ffmpeg_manager import get_ffmpeg_manager


class SubtitleError(Exception):
    pass


class SubtitleManager:
    """
    Handles extraction of subtitle streams from video files and
    prepares them for embedding or burning into output clips.
    """

    def __init__(self):
        self._mgr = get_ffmpeg_manager()

    def extract_subtitle(
        self,
        video_path: str,
        subtitle_track: SubtitleTrack,
        temp_dir: str,
        output_format: str = "srt",
    ) -> str:
        """
        Extract a subtitle stream from the source video.

        Args:
            video_path: Source video file path.
            subtitle_track: The subtitle track to extract.
            temp_dir: Directory to write extracted subtitle to.
            output_format: 'srt' or 'ass' (default 'srt').

        Returns:
            Path to extracted subtitle file.
        """
        out_path = str(Path(temp_dir) / f"subtitle_{subtitle_track.index}.{output_format}")

        cmd_args = [
            "-i", video_path,
            "-map", f"0:s:{subtitle_track.index}",
            "-c:s", "srt" if output_format == "srt" else "ass",
            out_path,
        ]

        proc = self._mgr.start_ffmpeg(cmd_args)
        stdout, stderr = proc.communicate(timeout=60)
        if proc.returncode != 0:
            raise SubtitleError(
                f"Failed to extract subtitle stream {subtitle_track.index}.\n"
                f"FFmpeg error: {stderr[-500:] if stderr else 'unknown'}"
            )

        if not Path(out_path).exists():
            raise SubtitleError(f"Subtitle extraction produced no output file: {out_path}")

        return out_path

    def extract_subtitle_for_burning(
        self,
        video_path: str,
        subtitle_track: SubtitleTrack,
        temp_dir: str,
    ) -> str:
        """
        Extract subtitle in ASS format for burning (supports Unicode/Hindi fonts).
        Falls back to SRT if ASS extraction fails.
        """
        # Image-based subtitles cannot be burned via text filter
        if subtitle_track.is_image_based:
            raise SubtitleError(
                f"The subtitle track '{subtitle_track.display_name}' uses an image-based format "
                f"({subtitle_track.codec}) which cannot be burned into video.\n"
                "Please select a text-based subtitle track or choose 'No subtitles'."
            )
        try:
            return self.extract_subtitle(video_path, subtitle_track, temp_dir, "ass")
        except SubtitleError:
            return self.extract_subtitle(video_path, subtitle_track, temp_dir, "srt")

    @staticmethod
    def build_burn_filter(subtitle_path: str) -> str:
        """
        Build the FFmpeg -vf filter string for burning subtitles.
        Escapes path for FFmpeg filter syntax.
        Includes force_style for UTF-8 / Unicode languages.
        """
        # Escape special characters in path for ffmpeg filter
        escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
        force_style = (
            "FontName=Noto Sans,"
            "FontSize=24,"
            "PrimaryColour=&HFFFFFF&,"
            "OutlineColour=&H000000&,"
            "Outline=2,"
            "Shadow=1"
        )
        return f"subtitles='{escaped}':force_style='{force_style}'"

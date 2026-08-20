"""Clip processing settings model."""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from video_automator.models.video_info import VideoInfo
from video_automator.models.audio_track import AudioTrack
from video_automator.models.subtitle_track import SubtitleTrack


class SubtitleMode(str, Enum):
    NO_SUBTITLES = "no_subtitles"
    EMBEDDED = "embedded"
    BURNED = "burned"


class OverwriteMode(str, Enum):
    OVERWRITE = "overwrite"
    SKIP = "skip"
    RENUMBER = "renumber"
    CANCEL = "cancel"


@dataclass
class ClipSettings:
    """Complete configuration for a clip generation job."""
    # Source
    source_video: Optional[VideoInfo] = None

    # Audio
    selected_audio: Optional[AudioTrack] = None

    # Subtitle
    selected_subtitle: Optional[SubtitleTrack] = None
    subtitle_mode: SubtitleMode = SubtitleMode.NO_SUBTITLES

    # Translation
    translate_subtitle: bool = False
    source_language: str = "English"
    target_language: str = "Hindi"
    translated_subtitle_path: Optional[str] = None

    # Clip Duration
    clip_duration_seconds: float = 60.0
    include_partial_clip: bool = True

    # Output
    output_dir: str = ""
    base_name: str = "clip"
    overwrite_mode: OverwriteMode = OverwriteMode.RENUMBER

    @property
    def total_clips(self) -> int:
        """Calculate total number of clips to generate."""
        if not self.source_video or self.clip_duration_seconds <= 0:
            return 0
        duration = self.source_video.duration_seconds
        full_clips = int(duration // self.clip_duration_seconds)
        remainder = duration % self.clip_duration_seconds
        if self.include_partial_clip and remainder > 0.5:
            return full_clips + 1
        return full_clips

    @property
    def pad_width(self) -> int:
        """Width for zero-padded clip numbering."""
        total = max(self.total_clips, 1)
        return max(3, len(str(total)))

    def clip_filename(self, index: int) -> str:
        """Generate filename for a clip by 1-based index."""
        return f"{self.base_name}_{str(index).zfill(self.pad_width)}.mp4"

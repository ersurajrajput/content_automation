"""Subtitle track model."""
from dataclasses import dataclass
from video_automator.models.audio_track import LANGUAGE_NAMES


@dataclass
class SubtitleTrack:
    """Represents a single subtitle stream in a video file."""
    index: int = 0          # zero-based index among subtitle streams
    stream_index: int = 0   # absolute stream index in the container
    codec: str = ""
    language_code: str = ""
    language_name: str = ""
    title: str = ""
    is_default: bool = False
    is_forced: bool = False

    def __post_init__(self):
        if not self.language_name and self.language_code:
            self.language_name = LANGUAGE_NAMES.get(
                self.language_code.lower(), self.language_code.upper()
            )

    @property
    def display_name(self) -> str:
        if self.title:
            return self.title
        if self.language_name:
            return self.language_name
        return f"Subtitle Track {self.index + 1}"

    @property
    def is_image_based(self) -> bool:
        """Image-based subtitles (e.g. PGS, VOBSUB) cannot be easily extracted."""
        return self.codec.lower() in ("hdmv_pgs_subtitle", "dvd_subtitle", "dvdsub")

    @property
    def is_text_based(self) -> bool:
        return not self.is_image_based

"""Audio track model."""
from dataclasses import dataclass

LANGUAGE_NAMES = {
    "eng": "English", "hin": "Hindi", "spa": "Spanish", "fra": "French",
    "deu": "German", "por": "Portuguese", "ben": "Bengali", "tam": "Tamil",
    "tel": "Telugu", "mar": "Marathi", "guj": "Gujarati", "jpn": "Japanese",
    "zho": "Chinese", "ara": "Arabic", "rus": "Russian", "kor": "Korean",
    "ita": "Italian", "pol": "Polish", "nld": "Dutch", "tur": "Turkish",
    "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
    "de": "German", "pt": "Portuguese", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "mr": "Marathi", "gu": "Gujarati", "ja": "Japanese",
}


@dataclass
class AudioTrack:
    """Represents a single audio stream in a video file."""
    index: int = 0          # zero-based index among audio streams
    stream_index: int = 0   # absolute stream index in the container
    codec: str = ""
    channels: int = 2
    sample_rate: int = 44100
    language_code: str = ""
    language_name: str = ""
    title: str = ""
    bit_rate: int = 0

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
        return f"Audio Track {self.index + 1}"

    @property
    def detail_str(self) -> str:
        parts = []
        if self.codec:
            parts.append(self.codec.upper())
        if self.channels:
            parts.append(f"{self.channels}ch")
        if self.sample_rate:
            parts.append(f"{self.sample_rate // 1000}kHz")
        return " · ".join(parts)

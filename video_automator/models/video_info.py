"""Video metadata model."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoInfo:
    """Holds full metadata about a video file."""
    path: str = ""
    filename: str = ""
    size_bytes: int = 0
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    video_codec: str = ""
    audio_codec: str = ""
    bit_rate: int = 0

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 * 1024 * 1024)

    @property
    def resolution_str(self) -> str:
        if self.width and self.height:
            return f"{self.width} × {self.height}"
        return "Unknown"

    @property
    def fps_str(self) -> str:
        if self.fps:
            return f"{self.fps:.2f}".rstrip("0").rstrip(".")
        return "Unknown"

    @property
    def exists(self) -> bool:
        return Path(self.path).exists() if self.path else False

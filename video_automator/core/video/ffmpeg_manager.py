"""FFmpeg/FFprobe binary manager."""
import subprocess
import shutil
import re
from typing import Optional, Tuple

from video_automator.config.settings import get_settings


class FFmpegNotFoundError(Exception):
    pass


class FFmpegManager:
    """Locate and validate ffmpeg/ffprobe executables."""

    def __init__(self):
        self._settings = get_settings()
        self._ffmpeg: Optional[str] = None
        self._ffprobe: Optional[str] = None

    def _find_executable(self, name: str, override: str = "") -> str:
        """Find executable by override path, then PATH."""
        if override and shutil.which(override):
            return override
        found = shutil.which(name)
        if found:
            return found
        raise FFmpegNotFoundError(
            f"'{name}' was not found on your system PATH.\n\n"
            "Please install FFmpeg:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS:         brew install ffmpeg\n"
            "  Windows:       Download from https://ffmpeg.org/download.html"
        )

    @property
    def ffmpeg(self) -> str:
        if not self._ffmpeg:
            self._ffmpeg = self._find_executable("ffmpeg", self._settings.ffmpeg_path)
        return self._ffmpeg

    @property
    def ffprobe(self) -> str:
        if not self._ffprobe:
            self._ffprobe = self._find_executable("ffprobe", self._settings.ffprobe_path)
        return self._ffprobe

    def validate(self) -> Tuple[bool, str]:
        """Check both binaries exist and return (ok, message)."""
        try:
            _ = self.ffmpeg
            _ = self.ffprobe
            return True, "FFmpeg and FFprobe are available."
        except FFmpegNotFoundError as e:
            return False, str(e)

    def run_ffprobe(self, args: list, timeout: int = 30) -> Tuple[str, str, int]:
        """Run ffprobe with given args. Returns (stdout, stderr, returncode)."""
        cmd = [self.ffprobe] + args
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return (
            result.stdout.decode("utf-8", errors="replace"),
            result.stderr.decode("utf-8", errors="replace"),
            result.returncode,
        )

    def start_ffmpeg(self, args: list) -> subprocess.Popen:
        """
        Start an FFmpeg process and return the Popen object.
        stderr is piped for progress parsing; stdout is PIPE.
        """
        cmd = [self.ffmpeg, "-y"] + args
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    @staticmethod
    def parse_progress_time(line: str) -> Optional[float]:
        """
        Parse a 'time=HH:MM:SS.mm' value from an ffmpeg stderr progress line.
        Returns seconds as float, or None if not found.
        """
        m = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)
        if m:
            h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
            return h * 3600 + mi * 60 + s
        return None


# Singleton
_ffmpeg_manager = None


def get_ffmpeg_manager() -> FFmpegManager:
    global _ffmpeg_manager
    if _ffmpeg_manager is None:
        _ffmpeg_manager = FFmpegManager()
    return _ffmpeg_manager

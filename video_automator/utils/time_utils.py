"""Time formatting utilities."""
import math


def format_seconds_to_hms(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_seconds_to_timecode(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for FFmpeg seek arguments."""
    if seconds < 0:
        seconds = 0
    total_ms = int(seconds * 1000)
    h = total_ms // 3_600_000
    m = (total_ms % 3_600_000) // 60_000
    s = (total_ms % 60_000) // 1_000
    ms = total_ms % 1_000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def format_duration_human(seconds: float) -> str:
    """Format as '1h 23m 45s' human-readable string."""
    if seconds < 0:
        seconds = 0
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)


def format_size_human(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    i = min(i, len(units) - 1)
    p = 1024 ** i
    s = size_bytes / p
    return f"{s:.1f} {units[i]}" if s < 10 else f"{s:.0f} {units[i]}"


def parse_duration_string(duration_str: str) -> float:
    """Parse HH:MM:SS.mmm or seconds string to float seconds."""
    try:
        return float(duration_str)
    except ValueError:
        pass
    try:
        parts = duration_str.strip().split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    except Exception:
        pass
    return 0.0


def eta_string(elapsed_seconds: float, completed: int, total: int) -> str:
    """Estimate remaining time as HH:MM:SS string."""
    if completed <= 0 or total <= 0:
        return "--:--"
    remaining = total - completed
    rate = elapsed_seconds / completed  # seconds per clip
    eta = rate * remaining
    return format_seconds_to_hms(eta)

"""Disk space utilities."""
import shutil
import os
from pathlib import Path


def get_free_disk_space(path: str) -> int:
    """Return free disk space in bytes for the filesystem at path."""
    try:
        p = Path(path)
        # Walk up to find an existing directory
        while not p.exists():
            p = p.parent
        usage = shutil.disk_usage(str(p))
        return usage.free
    except Exception:
        return 0


def estimate_clipping_space(
    source_size_bytes: int,
    source_duration_seconds: float,
    clip_duration_seconds: float,
    total_clips: int,
) -> int:
    """
    Estimate bytes needed for all clips.
    Uses source bit-rate as a proxy; burn-subtitle re-encodes may be smaller.
    Adds 10% buffer.
    """
    if source_duration_seconds <= 0:
        return 0
    bytes_per_second = source_size_bytes / source_duration_seconds
    estimated = bytes_per_second * clip_duration_seconds * total_clips
    return int(estimated * 1.10)  # 10% safety margin


def has_sufficient_space(output_dir: str, required_bytes: int) -> bool:
    """Return True if output_dir has at least required_bytes free."""
    free = get_free_disk_space(output_dir)
    return free >= required_bytes


def ensure_dir_exists(path: str) -> bool:
    """Create directory if it does not exist. Returns True on success."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def is_dir_writable(path: str) -> bool:
    """Check if directory is writable."""
    try:
        p = Path(path)
        if not p.exists():
            return False
        return os.access(str(p), os.W_OK)
    except Exception:
        return False

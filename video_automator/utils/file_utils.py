"""File utilities."""
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple


def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.strip(" .")
    return name or "clip"


def find_existing_conflicts(output_dir: str, base_name: str, total_clips: int, pad_width: int) -> List[str]:
    """Return list of filenames that already exist in output_dir."""
    conflicts = []
    out = Path(output_dir)
    for i in range(1, total_clips + 1):
        fname = f"{base_name}_{str(i).zfill(pad_width)}.mp4"
        if (out / fname).exists():
            conflicts.append(fname)
    return conflicts


def find_next_free_index(output_dir: str, base_name: str, pad_width: int) -> int:
    """
    Find the next sequential number that doesn't conflict.
    Scans for existing files matching base_name_NNN.mp4 pattern.
    """
    out = Path(output_dir)
    existing = set()
    pattern = re.compile(rf"^{re.escape(base_name)}_(\d+)\.mp4$", re.IGNORECASE)
    if out.exists():
        for f in out.iterdir():
            m = pattern.match(f.name)
            if m:
                existing.add(int(m.group(1)))
    n = 1
    while n in existing:
        n += 1
    return n


def generate_clip_filenames(
    base_name: str,
    start_index: int,
    total_clips: int,
    pad_width: int,
) -> List[str]:
    """Return list of output filenames for clips."""
    names = []
    for i in range(start_index, start_index + total_clips):
        names.append(f"{base_name}_{str(i).zfill(pad_width)}.mp4")
    return names


def create_temp_dir(prefix: str = "video_automator_") -> str:
    """Create and return a temporary directory path."""
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp_dir(temp_dir: str) -> None:
    """Remove a temporary directory and all its contents."""
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def format_file_list_preview(filenames: List[str], max_preview: int = 5) -> str:
    """Format a list of filenames for display (truncated)."""
    if not filenames:
        return "(none)"
    lines = filenames[:max_preview]
    result = "\n".join(lines)
    if len(filenames) > max_preview:
        result += f"\n... and {len(filenames) - max_preview} more"
    return result

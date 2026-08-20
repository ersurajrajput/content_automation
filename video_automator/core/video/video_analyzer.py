"""Video stream analyzer using FFprobe."""
import json
from typing import List, Optional, Tuple

from video_automator.models.video_info import VideoInfo
from video_automator.models.audio_track import AudioTrack
from video_automator.models.subtitle_track import SubtitleTrack
from video_automator.core.video.ffmpeg_manager import get_ffmpeg_manager
from video_automator.utils.time_utils import parse_duration_string


class VideoAnalysisError(Exception):
    pass


class VideoAnalyzer:
    """Uses FFprobe to extract full media metadata."""

    def __init__(self):
        self._mgr = get_ffmpeg_manager()

    def analyze(self, video_path: str) -> Tuple[VideoInfo, List[AudioTrack], List[SubtitleTrack]]:
        """
        Analyze a video file and return (VideoInfo, [AudioTrack], [SubtitleTrack]).
        Raises VideoAnalysisError on failure.
        """
        import os
        from pathlib import Path

        if not Path(video_path).exists():
            raise VideoAnalysisError(f"File does not exist: {video_path}")

        args = [
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]
        stdout, stderr, code = self._mgr.run_ffprobe(args, timeout=60)

        if code != 0:
            raise VideoAnalysisError(
                f"FFprobe failed to analyze the video.\n\nDetails:\n{stderr[:500]}"
            )

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise VideoAnalysisError(f"Failed to parse FFprobe output: {e}")

        streams = data.get("streams", [])
        fmt = data.get("format", {})

        video_info = self._parse_video_info(video_path, streams, fmt)
        audio_tracks = self._parse_audio_tracks(streams)
        subtitle_tracks = self._parse_subtitle_tracks(streams)

        return video_info, audio_tracks, subtitle_tracks

    def _parse_video_info(self, path: str, streams: list, fmt: dict) -> VideoInfo:
        from pathlib import Path
        p = Path(path)

        # Duration: prefer format-level duration
        duration = parse_duration_string(fmt.get("duration", "0"))
        bit_rate = int(fmt.get("bit_rate", 0) or 0)
        size_bytes = int(fmt.get("size", 0) or p.stat().st_size)

        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"), {}
        )
        audio_stream = next(
            (s for s in streams if s.get("codec_type") == "audio"), {}
        )

        # FPS from avg_frame_rate or r_frame_rate
        fps = 0.0
        fr = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = fr.split("/")
            fps = float(num) / float(den) if float(den) else 0.0
        except Exception:
            fps = 0.0

        # Duration fallback from video stream
        if duration <= 0:
            duration = parse_duration_string(video_stream.get("duration", "0"))

        return VideoInfo(
            path=str(p.resolve()),
            filename=p.name,
            size_bytes=size_bytes,
            duration_seconds=duration,
            width=int(video_stream.get("width", 0) or 0),
            height=int(video_stream.get("height", 0) or 0),
            fps=round(fps, 3),
            video_codec=video_stream.get("codec_name", "").upper(),
            audio_codec=audio_stream.get("codec_name", "").upper(),
            bit_rate=bit_rate,
        )

    def _parse_audio_tracks(self, streams: list) -> List[AudioTrack]:
        tracks = []
        audio_idx = 0
        for stream in streams:
            if stream.get("codec_type") != "audio":
                continue
            tags = stream.get("tags", {})
            lang_code = (
                tags.get("language") or
                tags.get("LANGUAGE") or
                tags.get("lang") or
                ""
            ).strip()
            title = (
                tags.get("title") or
                tags.get("TITLE") or
                ""
            ).strip()

            track = AudioTrack(
                index=audio_idx,
                stream_index=int(stream.get("index", 0)),
                codec=stream.get("codec_name", ""),
                channels=int(stream.get("channels", 2) or 2),
                sample_rate=int(stream.get("sample_rate", 44100) or 44100),
                language_code=lang_code,
                title=title,
                bit_rate=int(stream.get("bit_rate", 0) or 0),
            )
            tracks.append(track)
            audio_idx += 1
        return tracks

    def _parse_subtitle_tracks(self, streams: list) -> List[SubtitleTrack]:
        tracks = []
        sub_idx = 0
        for stream in streams:
            if stream.get("codec_type") != "subtitle":
                continue
            tags = stream.get("tags", {})
            disposition = stream.get("disposition", {})
            lang_code = (
                tags.get("language") or
                tags.get("LANGUAGE") or
                tags.get("lang") or
                ""
            ).strip()
            title = (
                tags.get("title") or
                tags.get("TITLE") or
                ""
            ).strip()

            track = SubtitleTrack(
                index=sub_idx,
                stream_index=int(stream.get("index", 0)),
                codec=stream.get("codec_name", ""),
                language_code=lang_code,
                title=title,
                is_default=bool(disposition.get("default", False)),
                is_forced=bool(disposition.get("forced", False)),
            )
            tracks.append(track)
            sub_idx += 1
        return tracks

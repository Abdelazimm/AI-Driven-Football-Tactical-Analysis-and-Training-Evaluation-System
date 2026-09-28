"""
Media probe service.
Extracts authoritative container, codec, and dimensional metadata from uploaded media
using ffprobe subprocess. Client-declared metadata is NEVER trusted for validation.

CRITICAL: FPS must be extracted from video metadata, never hardcoded.
CRITICAL: Duration comes from the actual container, never from the client.
"""
import json
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field


class ProbeStatus(str, Enum):
    """Authoritative probe outcome status."""
    SUCCESS = "SUCCESS"
    INVALID_CONTAINER = "INVALID_CONTAINER"
    NO_VIDEO_STREAM = "NO_VIDEO_STREAM"
    CORRUPT_FILE = "CORRUPT_FILE"
    FFPROBE_NOT_AVAILABLE = "FFPROBE_NOT_AVAILABLE"
    PROBE_TIMEOUT = "PROBE_TIMEOUT"
    PROBE_ERROR = "PROBE_ERROR"


class MediaProbeResult(BaseModel):
    """
    Authoritative media metadata extracted from the actual stored object.
    All fields are server-verified — never client-declared.
    """
    container_format: Optional[str] = Field(None, description="ffprobe format_name, e.g. 'mov,mp4,m4a,3gp,3g2,mj2'")
    duration_seconds: Optional[float] = Field(None, description="Authoritative duration from container")
    width: Optional[int] = Field(None, description="Video frame width")
    height: Optional[int] = Field(None, description="Video frame height")
    fps: Optional[float] = Field(None, description="Video frame rate (frames per second)")
    video_codec: Optional[str] = Field(None, description="Video codec name, e.g. 'h264'")
    audio_codec: Optional[str] = Field(None, description="Audio codec name, e.g. 'aac', None if no audio")
    has_video: bool = Field(default=False, description="Whether a video stream was found")
    has_audio: bool = Field(default=False, description="Whether an audio stream was found")
    probe_status: ProbeStatus = Field(..., description="Probe outcome status")
    error_message: Optional[str] = Field(None, description="Diagnostic message on failure")


# =============================================================================
# CONSTANTS
# =============================================================================

# ffprobe subprocess timeout in seconds
FFPROBE_TIMEOUT_SECONDS = 30

# Supported video container format families (ffprobe format_name values)
# These are the format_name strings ffprobe reports for MP4 and MOV containers
SUPPORTED_VIDEO_CONTAINERS = {
    "mov,mp4,m4a,3gp,3g2,mj2",  # MP4/MOV family
    "mp4",
    "mov",
    "matroska,webm",  # MKV/WebM (common re-encode target)
}


# =============================================================================
# ABSTRACT INTERFACE
# =============================================================================

class MediaProbeService(ABC):
    """Abstract interface for extracting authoritative media metadata."""

    @abstractmethod
    def probe(self, file_path_or_url: str) -> MediaProbeResult:
        """
        Probe a local file or URL for container/codec/dimensional metadata.
        Returns a MediaProbeResult with probe_status indicating success or failure type.
        NEVER raises on invalid media — returns a typed failure result instead.
        """
        pass


# =============================================================================
# FFPROBE PRODUCTION IMPLEMENTATION
# =============================================================================

class FFProbeMediaProbeService(MediaProbeService):
    """
    Production media probe using ffprobe subprocess.
    
    ffprobe natively supports HTTP(S) URLs, so we pass signed download URLs
    directly — it reads only container headers (a few KB), not the entire file.
    
    Probe location rationale: Local ffprobe is used because:
    1. ffprobe is already installed in the development/deployment environment
    2. It only reads container headers (~100ms), not the entire file
    3. Avoids Modal cold-start latency for a sub-second operation
    4. Keeps media validation in the control plane, separate from M1/M2/M3 methodology execution
    """

    def __init__(self, ffprobe_path: Optional[str] = None):
        self._ffprobe_path = ffprobe_path or shutil.which("ffprobe")

    def probe(self, file_path_or_url: str) -> MediaProbeResult:
        if not self._ffprobe_path:
            return MediaProbeResult(
                probe_status=ProbeStatus.FFPROBE_NOT_AVAILABLE,
                error_message="ffprobe executable not found in PATH.",
            )

        try:
            cmd = [
                self._ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path_or_url,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=FFPROBE_TIMEOUT_SECONDS,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip() if result.stderr else ""
                # ffprobe returns non-zero for invalid/corrupt files
                return MediaProbeResult(
                    probe_status=ProbeStatus.INVALID_CONTAINER,
                    error_message=f"ffprobe exited with code {result.returncode}: {stderr[:200]}",
                )

            return self._parse_ffprobe_output(result.stdout)

        except subprocess.TimeoutExpired:
            return MediaProbeResult(
                probe_status=ProbeStatus.PROBE_TIMEOUT,
                error_message=f"ffprobe timed out after {FFPROBE_TIMEOUT_SECONDS}s.",
            )
        except json.JSONDecodeError as je:
            return MediaProbeResult(
                probe_status=ProbeStatus.CORRUPT_FILE,
                error_message=f"ffprobe produced invalid JSON output: {je}",
            )
        except Exception as ex:
            return MediaProbeResult(
                probe_status=ProbeStatus.PROBE_ERROR,
                error_message=f"Unexpected probe error: {type(ex).__name__}: {str(ex)[:200]}",
            )

    def _parse_ffprobe_output(self, stdout: str) -> MediaProbeResult:
        """Parse ffprobe JSON output into MediaProbeResult."""
        data = json.loads(stdout)

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        container_format = format_info.get("format_name")
        # Duration from format level (most reliable)
        raw_duration = format_info.get("duration")
        duration_seconds = self._safe_float(raw_duration)

        # Find video and audio streams
        video_stream = None
        audio_stream = None
        for stream in streams:
            codec_type = stream.get("codec_type", "")
            if codec_type == "video" and video_stream is None:
                video_stream = stream
            elif codec_type == "audio" and audio_stream is None:
                audio_stream = stream

        has_video = video_stream is not None
        has_audio = audio_stream is not None

        if not has_video:
            return MediaProbeResult(
                container_format=container_format,
                duration_seconds=duration_seconds,
                has_video=False,
                has_audio=has_audio,
                audio_codec=audio_stream.get("codec_name") if audio_stream else None,
                probe_status=ProbeStatus.NO_VIDEO_STREAM,
                error_message="No video stream found in container.",
            )

        # Extract video metadata
        video_codec = video_stream.get("codec_name")
        width = self._safe_int(video_stream.get("width"))
        height = self._safe_int(video_stream.get("height"))

        # FPS extraction: prefer avg_frame_rate, fallback to r_frame_rate
        fps = self._parse_frame_rate(
            video_stream.get("avg_frame_rate"),
            video_stream.get("r_frame_rate"),
        )

        # If duration not at format level, try stream level
        if duration_seconds is None or duration_seconds <= 0:
            stream_duration = video_stream.get("duration")
            duration_seconds = self._safe_float(stream_duration)

        audio_codec = audio_stream.get("codec_name") if audio_stream else None

        return MediaProbeResult(
            container_format=container_format,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            fps=fps,
            video_codec=video_codec,
            audio_codec=audio_codec,
            has_video=True,
            has_audio=has_audio,
            probe_status=ProbeStatus.SUCCESS,
        )

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float, returning None for invalid/non-finite values."""
        if value is None:
            return None
        try:
            f = float(value)
            if f != f:  # NaN check
                return None
            if f == float("inf") or f == float("-inf"):
                return None
            return f
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Safely convert to int, returning None for invalid values."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_frame_rate(avg_rate: Optional[str], r_rate: Optional[str]) -> Optional[float]:
        """
        Parse ffprobe frame rate strings (e.g. '30000/1001', '30/1', '0/0').
        Returns None for invalid/zero/non-finite values.
        """
        for rate_str in (avg_rate, r_rate):
            if not rate_str:
                continue
            try:
                if "/" in rate_str:
                    num, den = rate_str.split("/", 1)
                    num_f = float(num)
                    den_f = float(den)
                    if den_f == 0:
                        continue
                    fps = num_f / den_f
                else:
                    fps = float(rate_str)

                if fps <= 0 or fps != fps or fps == float("inf"):
                    continue
                return fps
            except (ValueError, TypeError, ZeroDivisionError):
                continue
        return None


# =============================================================================
# IN-MEMORY TESTING IMPLEMENTATION
# =============================================================================

class InMemoryMediaProbeService(MediaProbeService):
    """
    Test stub with configurable probe results.
    Allows tests to simulate valid, invalid, corrupt, and timeout probe outcomes.
    """

    def __init__(self):
        self._results: Dict[str, MediaProbeResult] = {}
        self._default_result: Optional[MediaProbeResult] = None

    def set_probe_result(self, url_or_path: str, result: MediaProbeResult) -> None:
        """Configure probe result for a specific URL or file path."""
        self._results[url_or_path] = result

    def set_default_result(self, result: MediaProbeResult) -> None:
        """Configure default probe result for any unregistered path."""
        self._default_result = result

    def probe(self, file_path_or_url: str) -> MediaProbeResult:
        if file_path_or_url in self._results:
            return self._results[file_path_or_url]
        if self._default_result is not None:
            return self._default_result
        return MediaProbeResult(
            probe_status=ProbeStatus.PROBE_ERROR,
            error_message=f"No probe result configured for '{file_path_or_url}'.",
        )

    def clear(self) -> None:
        self._results.clear()
        self._default_result = None

"""FFprobe media inspector adapter.

Implements AudioInspectorPort to accurately measure audio files and verify
rendered video streams and metadata.
"""

import json
import os
import shutil
import subprocess
from space_motion_studio.application.dtos import OutputMediaMetadataDTO
from space_motion_studio.application.ports.audio_inspector import AudioInspectorPort
from space_motion_studio.domain.errors import ResourceNotFoundError, ValidationError


def resolve_ffprobe_executable() -> str:
    """Resolve ffprobe executable on Windows and Unix systems."""
    exe = shutil.which("ffprobe")
    if exe:
        return exe
    for candidate in ("ffprobe.exe", "ffprobe"):
        if shutil.which(candidate):
            return candidate
    raise ResourceNotFoundError("ffprobe executable could not be resolved on PATH")


class FFprobeInspector(AudioInspectorPort):
    """Inspects audio and video files using ffprobe."""

    def __init__(self, ffprobe_exe: str | None = None) -> None:
        self.ffprobe_exe = ffprobe_exe or resolve_ffprobe_executable()

    def inspect_audio(self, file_path: str) -> tuple[float, int, int]:
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(f"Audio file not found: {file_path}")

        cmd = [
            self.ffprobe_exe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=duration,sample_rate,channels:format=duration",
            "-of",
            "json",
            file_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            data = json.loads(result.stdout)
        except subprocess.CalledProcessError as exc:
            raise ValidationError(f"ffprobe failed to inspect audio {file_path}: {exc.stderr}") from exc
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid ffprobe output: {exc}") from exc

        streams = data.get("streams", [])
        duration_str = None
        sample_rate = 44100
        channels = 2

        if streams:
            stream = streams[0]
            duration_str = stream.get("duration")
            sample_rate = int(stream.get("sample_rate", 44100))
            channels = int(stream.get("channels", 2))

        if not duration_str and "format" in data:
            duration_str = data["format"].get("duration")

        if not duration_str:
            raise ValidationError(f"Could not determine audio duration for {file_path}")

        return float(duration_str), sample_rate, channels

    def inspect_video(self, file_path: str, orientation: str = "landscape") -> OutputMediaMetadataDTO:
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(f"Video file not found: {file_path}")

        cmd = [
            self.ffprobe_exe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate:format=duration,size",
            "-of",
            "json",
            file_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            data = json.loads(result.stdout)
        except subprocess.CalledProcessError as exc:
            raise ValidationError(f"ffprobe failed to inspect video {file_path}: {exc.stderr}") from exc
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid ffprobe output: {exc}") from exc

        video_stream = None
        audio_stream = None

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream

        if not video_stream:
            raise ValidationError(f"No video stream found in {file_path}")

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        video_codec = video_stream.get("codec_name", "")
        pix_fmt = video_stream.get("pix_fmt", "")

        # Compute FPS from r_frame_rate e.g. "30/1"
        r_rate = video_stream.get("r_frame_rate", "30/1")
        if "/" in r_rate:
            num, den = r_rate.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 30.0
        else:
            fps = float(r_rate)

        # Parse total frames
        nb_frames_str = video_stream.get("nb_frames")
        if nb_frames_str and nb_frames_str.isdigit():
            total_frames = int(nb_frames_str)
        else:
            # Fallback if container does not store nb_frames in header
            dur_str = data.get("format", {}).get("duration", "0")
            total_frames = round(float(dur_str) * fps)

        duration_seconds = float(data.get("format", {}).get("duration", 0.0))
        file_size_bytes = int(data.get("format", {}).get("size", os.path.getsize(file_path)))

        audio_codec = audio_stream.get("codec_name", "aac") if audio_stream else "none"
        audio_sample_rate = int(audio_stream.get("sample_rate", 0)) if audio_stream else 0

        return OutputMediaMetadataDTO(
            path=file_path,
            orientation=orientation,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            total_frames=total_frames,
            video_codec=video_codec,
            pixel_format=pix_fmt,
            audio_codec=audio_codec,
            audio_sample_rate=audio_sample_rate,
            file_size_bytes=file_size_bytes,
        )

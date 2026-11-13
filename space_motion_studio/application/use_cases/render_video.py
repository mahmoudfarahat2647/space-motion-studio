"""Render video use case.

Validates that all referenced assets exist and match digests, delegates rendering
to the VideoRendererPort, validates output streams with media inspector,
and atomically promotes the final MP4 export.
Follows Clean Architecture: no direct filesystem (os.path) operations in application layer.
"""

from space_motion_studio.application.dtos import (
    OutputMediaMetadataDTO,
    RenderManifestDTO,
)
from space_motion_studio.application.ports.audio_inspector import AudioInspectorPort
from space_motion_studio.application.ports.run_storage import RunStoragePort
from space_motion_studio.application.ports.video_renderer import VideoRendererPort
from space_motion_studio.domain.errors import RenderError, ResourceNotFoundError, ValidationError


class RenderVideoUseCase:
    """Coordinates video rendering and verification."""

    def __init__(
        self,
        storage: RunStoragePort,
        renderer: VideoRendererPort,
        inspector: AudioInspectorPort,
    ) -> None:
        self._storage = storage
        self._renderer = renderer
        self._inspector = inspector

    def execute(
        self,
        manifest: RenderManifestDTO,
        manifest_file_path: str,
        orientation: str = "landscape",
        width: int = 1920,
        height: int = 1080,
    ) -> OutputMediaMetadataDTO:
        run_id = manifest.run_id
        run_dir = self._storage.get_run_dir(run_id)

        # 1. Validate that all referenced assets exist and digests match
        for asset in manifest.assets:
            if not self._storage.verify_run_asset(run_id, asset.path, asset.digest):
                raise ResourceNotFoundError(
                    f"Asset {asset.path} does not exist or digest mismatch in run {run_id}"
                )

        # 2. Prepare paths via storage port
        final_filename = f"{orientation}.mp4"
        final_output_path = self._storage.get_export_path(run_id, final_filename)
        temp_output_path = self._storage.get_export_temp_path(run_id, f"{orientation}.tmp.mp4")

        # 3. Call renderer (Remotion CLI)
        self._renderer.render(
            manifest_path=manifest_file_path,
            public_dir=run_dir,
            output_path=temp_output_path,
            orientation=orientation,
            fps=manifest.fps,
            width=width,
            height=height,
        )

        if not self._storage.file_exists(temp_output_path):
            raise RenderError(f"Rendering failed: expected output file {temp_output_path} not found")

        # 4. Inspect rendered video
        metadata = self._inspector.inspect_video(temp_output_path, orientation=orientation)

        # 5. Validate output criteria (SPEC.md Decision 16)
        if metadata.width != width or metadata.height != height:
            raise ValidationError(
                f"Output dimensions mismatch: expected {width}x{height}, got {metadata.width}x{metadata.height}",
                "dimensions",
            )
        if abs(metadata.fps - manifest.fps) > 0.05:
            raise ValidationError(
                f"Output FPS mismatch: expected {manifest.fps}, got {metadata.fps}",
                "fps",
            )
        if "h264" not in metadata.video_codec.lower():
            raise ValidationError(
                f"Output video codec mismatch: expected h264, got {metadata.video_codec}",
                "videoCodec",
            )
        if metadata.pixel_format.lower() != "yuv420p":
            raise ValidationError(
                f"Output pixel format mismatch: expected yuv420p, got {metadata.pixel_format}",
                "pixelFormat",
            )
        if "aac" not in metadata.audio_codec.lower():
            raise ValidationError(
                f"Output audio codec mismatch: expected aac, got {metadata.audio_codec}",
                "audioCodec",
            )
        if metadata.audio_sample_rate != 48000:
            raise ValidationError(
                f"Output audio sample rate mismatch: expected 48000 Hz, got {metadata.audio_sample_rate}",
                "audioSampleRate",
            )
        if metadata.total_frames != manifest.total_frame_count:
            raise ValidationError(
                f"Output frame count mismatch: expected {manifest.total_frame_count}, got {metadata.total_frames}",
                "totalFrames",
            )

        # 6. Atomically promote temp file to final output
        self._storage.atomic_publish(temp_output_path, final_output_path)

        # Return metadata with final path
        return OutputMediaMetadataDTO(
            path=final_output_path,
            orientation=metadata.orientation,
            width=metadata.width,
            height=metadata.height,
            fps=metadata.fps,
            duration_seconds=metadata.duration_seconds,
            total_frames=metadata.total_frames,
            video_codec=metadata.video_codec,
            pixel_format=metadata.pixel_format,
            audio_codec=metadata.audio_codec,
            audio_sample_rate=metadata.audio_sample_rate,
            file_size_bytes=self._storage.get_file_size(final_output_path),
        )

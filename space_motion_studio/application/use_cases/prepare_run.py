"""Prepare run use case.

Creates an isolated run, takes snapshots of input and assets, computes digests,
measures audio durations, compiles timeline schedule, and builds the prepared render manifest.
"""

from typing import Callable
from space_motion_studio.application.dtos import (
    AssetRecordDTO,
    PreparedSceneDTO,
    RenderManifestDTO,
    StoryboardDTO,
)
from space_motion_studio.application.ports.audio_inspector import AudioInspectorPort
from space_motion_studio.application.ports.run_storage import RunStoragePort
from space_motion_studio.application.use_cases.compile_timeline import CompileTimelineUseCase
from space_motion_studio.domain.errors import ResourceNotFoundError, ValidationError


class PrepareRunUseCase:
    """Coordinates preparation of a video run."""

    def __init__(
        self,
        storage: RunStoragePort,
        audio_inspector: AudioInspectorPort,
        timeline_compiler: CompileTimelineUseCase,
        serialize_manifest: Callable[[RenderManifestDTO], str],
    ) -> None:
        self._storage = storage
        self._audio_inspector = audio_inspector
        self._timeline_compiler = timeline_compiler
        self._serialize_manifest = serialize_manifest

    def execute(
        self,
        run_id: str,
        storyboard: StoryboardDTO,
        storyboard_json: str,
        render_seed: int = 42,
        fps: int = 30,
        trailing_pause_seconds: float = 0.4,
    ) -> RenderManifestDTO:
        if not storyboard.scenes:
            raise ValidationError("Storyboard must contain at least one scene", "scenes")

        # 1. Initialize run directory and snapshot input storyboard
        self._storage.create_run(run_id)
        _, input_digest = self._storage.save_storyboard_snapshot(run_id, storyboard_json)

        # 2. Process and copy assets into run, measuring audio
        prepared_scenes: list[PreparedSceneDTO] = []
        assets_map: dict[str, AssetRecordDTO] = {}
        audio_durations: list[float] = []

        # Always bundle font
        # The font should be copied to run assets
        # We will collect per-scene audio and illustrations
        for idx, scene in enumerate(storyboard.scenes):
            if not scene.narration_audio:
                raise ValidationError(
                    f"Scene {scene.id} missing required narration audio path",
                    f"scenes[{idx}].narrationAudio",
                )

            # Copy audio into run
            dest_audio_rel = f"assets/audio/{scene.id}.mp3"
            dest_audio_abs, audio_digest = self._storage.copy_asset_to_run(
                run_id, scene.narration_audio, dest_audio_rel
            )
            duration, _, _ = self._audio_inspector.inspect_audio(dest_audio_abs)
            audio_durations.append(duration)

            assets_map[dest_audio_rel] = AssetRecordDTO(
                path=dest_audio_rel,
                digest=audio_digest,
                media_type="audio/mp3",
                provenance=scene.narration_audio,
                attribution="Narrated audio",
            )

            # Copy illustration if present
            dest_illustration_rel: str | None = None
            illustration_digest: str | None = None
            if scene.illustration:
                dest_illustration_rel = f"assets/illustrations/{scene.id}.svg"
                _, illustration_digest = self._storage.copy_asset_to_run(
                    run_id, scene.illustration, dest_illustration_rel
                )
                assets_map[dest_illustration_rel] = AssetRecordDTO(
                    path=dest_illustration_rel,
                    digest=illustration_digest,
                    media_type="image/svg+xml",
                    provenance=scene.illustration,
                    attribution="Local vector illustration",
                )

        # 3. Compile timeline
        timeline = self._timeline_compiler.execute(
            audio_durations=audio_durations,
            fps=fps,
            trailing_pause_seconds=trailing_pause_seconds,
        )

        for idx, scene in enumerate(storyboard.scenes):
            dest_audio_rel = f"assets/audio/{scene.id}.mp3"
            audio_record = assets_map[dest_audio_rel]
            dest_illustration_rel = f"assets/illustrations/{scene.id}.svg" if scene.illustration else None
            illustration_record = assets_map.get(dest_illustration_rel) if dest_illustration_rel else None

            schedule = timeline.scenes[idx]
            prepared_scenes.append(
                PreparedSceneDTO(
                    id=scene.id,
                    narration=scene.narration,
                    on_screen_title=scene.on_screen_title,
                    template=scene.template,
                    template_parameters=scene.template_parameters,
                    animation_preset=scene.animation_preset,
                    sound_effect=scene.sound_effect,
                    audio_file=dest_audio_rel,
                    audio_digest=audio_record.digest,
                    measured_audio_duration=audio_durations[idx],
                    start_frame=schedule.start_frame,
                    audio_frame_count=schedule.audio_frame_count,
                    scene_frame_count=schedule.scene_frame_count,
                    trailing_pause_frames=schedule.trailing_pause_frames,
                    illustration_file=dest_illustration_rel,
                    illustration_digest=illustration_record.digest if illustration_record else None,
                )
            )

        manifest = RenderManifestDTO(
            schema_version="1.0.0",
            run_id=run_id,
            input_digest=input_digest,
            template_version="1.0.0",
            render_seed=render_seed,
            fps=fps,
            total_frame_count=timeline.total_frame_count,
            scenes=tuple(prepared_scenes),
            assets=tuple(assets_map.values()),
            theme=storyboard.theme,
        )

        # Save manifest
        manifest_json = self._serialize_manifest(manifest)
        self._storage.save_manifest(run_id, manifest_json)

        return manifest

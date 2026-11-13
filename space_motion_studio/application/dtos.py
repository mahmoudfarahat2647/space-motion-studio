"""Application-owned Data Transfer Objects (DTOs).

In Clean Architecture, data crossing boundaries between application use cases
and outer layers (adapters, UI, CLI) uses simple data structures (DTOs).
Entities do not leak outside the domain/application boundary.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ThemeDTO:
    bg_primary: str = "#050713"
    accent_primary: str = "#38bdf8"
    accent_secondary: str = "#f59e0b"
    text_primary: str = "#ffffff"


@dataclass(frozen=True)
class SceneDTO:
    id: str
    narration: str
    on_screen_title: str
    visual_intent: str
    template: str
    template_parameters: Mapping[str, Any]
    animation_preset: str
    sound_effect: str
    illustration: str | None = None
    narration_audio: str | None = None


@dataclass(frozen=True)
class StoryboardDTO:
    schema_version: str
    topic: str
    project_title: str
    locale: str
    duration_target: float
    theme: ThemeDTO
    scenes: tuple[SceneDTO, ...]


@dataclass(frozen=True)
class PreparedSceneDTO:
    id: str
    narration: str
    on_screen_title: str
    template: str
    template_parameters: Mapping[str, Any]
    animation_preset: str
    sound_effect: str
    audio_file: str
    audio_digest: str
    measured_audio_duration: float
    start_frame: int
    audio_frame_count: int
    scene_frame_count: int
    trailing_pause_frames: int
    illustration_file: str | None = None
    illustration_digest: str | None = None


@dataclass(frozen=True)
class AssetRecordDTO:
    path: str
    digest: str
    media_type: str
    provenance: str
    attribution: str


@dataclass(frozen=True)
class RenderManifestDTO:
    schema_version: str
    run_id: str
    input_digest: str
    template_version: str
    render_seed: int
    fps: int
    total_frame_count: int
    scenes: tuple[PreparedSceneDTO, ...]
    assets: tuple[AssetRecordDTO, ...]
    theme: ThemeDTO


@dataclass(frozen=True)
class OutputMediaMetadataDTO:
    path: str
    orientation: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    total_frames: int
    video_codec: str
    pixel_format: str
    audio_codec: str
    audio_sample_rate: int
    file_size_bytes: int


@dataclass(frozen=True)
class RunStageDTO:
    name: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class RunReportDTO:
    run_id: str
    operation: str
    status: str
    input_digest: str
    stages: tuple[RunStageDTO, ...]
    outputs: tuple[OutputMediaMetadataDTO, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    asset_credits: tuple[str, ...] = field(default_factory=tuple)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class PreflightCheckDTO:
    name: str
    passed: bool
    version: str | None
    message: str


@dataclass(frozen=True)
class PreflightReportDTO:
    all_passed: bool
    checks: tuple[PreflightCheckDTO, ...]

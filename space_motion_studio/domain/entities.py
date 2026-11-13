"""Domain entities and value objects for Space Motion Studio.

Pure business models with no dependencies on external frameworks, databases,
or outer layers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Orientation(str, Enum):
    LANDSCAPE = "landscape"
    VERTICAL = "vertical"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunOverallStatus(str, Enum):
    PREPARED = "prepared"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class Theme:
    bg_primary: str = "#050713"
    accent_primary: str = "#38bdf8"
    accent_secondary: str = "#f59e0b"
    text_primary: str = "#ffffff"


@dataclass(frozen=True)
class Scene:
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
class Storyboard:
    schema_version: str
    topic: str
    project_title: str
    locale: str
    duration_target: float
    theme: Theme
    scenes: tuple[Scene, ...]


@dataclass(frozen=True)
class PreparedScene:
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
class AssetRecord:
    path: str
    digest: str
    media_type: str
    provenance: str
    attribution: str


@dataclass(frozen=True)
class RenderManifest:
    schema_version: str
    run_id: str
    input_digest: str
    template_version: str
    render_seed: int
    fps: int
    total_frame_count: int
    scenes: tuple[PreparedScene, ...]
    assets: tuple[AssetRecord, ...]
    theme: Theme


@dataclass(frozen=True)
class RenderRequest:
    run_id: str
    orientation: Orientation
    fps: int = 30
    width: int = 1920
    height: int = 1080


@dataclass(frozen=True)
class OutputMediaMetadata:
    path: str
    orientation: Orientation
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
class RunStage:
    name: str
    status: StageStatus
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class RunReport:
    run_id: str
    operation: str
    status: RunOverallStatus
    input_digest: str
    stages: tuple[RunStage, ...]
    outputs: tuple[OutputMediaMetadata, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    asset_credits: tuple[str, ...] = field(default_factory=tuple)
    created_at: str | None = None
    updated_at: str | None = None

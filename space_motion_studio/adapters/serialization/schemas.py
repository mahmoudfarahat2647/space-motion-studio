"""Pydantic schemas for versioned camelCase JSON serialization and validation.

In Clean Architecture, Pydantic is an adapter tool for boundary validation.
It converts external camelCase JSON into validated data and forbids unknown fields.
"""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseContractModel(BaseModel):
    """Base model enforcing camelCase aliases and forbidding unknown fields."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class ThemeSchema(BaseContractModel):
    bg_primary: str = "#050713"
    accent_primary: str = "#38bdf8"
    accent_secondary: str = "#f59e0b"
    text_primary: str = "#ffffff"


class SceneSchema(BaseContractModel):
    id: str
    narration: str
    on_screen_title: str
    visual_intent: str
    template: str
    template_parameters: dict[str, Any] = Field(default_factory=dict)
    animation_preset: str
    sound_effect: str
    illustration: str | None = None
    narration_audio: str | None = None


class StoryboardSchema(BaseContractModel):
    schema_version: Literal["1.0.0"]
    topic: str
    project_title: str
    locale: str = "ar-EG"
    duration_target: float = Field(gt=0)
    theme: ThemeSchema = Field(default_factory=ThemeSchema)
    scenes: list[SceneSchema] = Field(min_length=1)


class PreparedSceneSchema(BaseContractModel):
    id: str
    narration: str
    on_screen_title: str
    template: str
    template_parameters: dict[str, Any] = Field(default_factory=dict)
    animation_preset: str
    sound_effect: str
    audio_file: str
    audio_digest: str
    measured_audio_duration: float = Field(ge=0)
    start_frame: int = Field(ge=0)
    audio_frame_count: int = Field(gt=0)
    scene_frame_count: int = Field(gt=0)
    trailing_pause_frames: int = Field(ge=0)
    illustration_file: str | None = None
    illustration_digest: str | None = None


class AssetRecordSchema(BaseContractModel):
    path: str
    digest: str
    media_type: str
    provenance: str
    attribution: str


class RenderManifestSchema(BaseContractModel):
    schema_version: Literal["1.0.0"]
    run_id: str
    input_digest: str
    template_version: str = "1.0.0"
    render_seed: int = 42
    fps: int = Field(default=30, gt=0)
    total_frame_count: int = Field(gt=0)
    scenes: list[PreparedSceneSchema] = Field(min_length=1)
    assets: list[AssetRecordSchema] = Field(default_factory=list)
    theme: ThemeSchema = Field(default_factory=ThemeSchema)


class OutputMediaMetadataSchema(BaseContractModel):
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


class RunStageSchema(BaseContractModel):
    name: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class RunReportSchema(BaseContractModel):
    run_id: str
    operation: str
    status: str
    input_digest: str
    stages: list[RunStageSchema]
    outputs: list[OutputMediaMetadataSchema]
    warnings: list[str] = Field(default_factory=list)
    asset_credits: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

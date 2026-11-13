"""Mapper between Pydantic schemas and Application DTOs.

Provides functions to validate JSON strings and map to/from application DTOs.
"""

import json
from pydantic import ValidationError as PydanticValidationError
from space_motion_studio.adapters.serialization.schemas import (
    AssetRecordSchema,
    OutputMediaMetadataSchema,
    PreparedSceneSchema,
    RenderManifestSchema,
    RunReportSchema,
    RunStageSchema,
    SceneSchema,
    StoryboardSchema,
    ThemeSchema,
)
from space_motion_studio.application.dtos import (
    AssetRecordDTO,
    OutputMediaMetadataDTO,
    PreparedSceneDTO,
    RenderManifestDTO,
    RunReportDTO,
    RunStageDTO,
    SceneDTO,
    StoryboardDTO,
    ThemeDTO,
)
from space_motion_studio.domain.errors import ValidationError


def _format_pydantic_error(exc: PydanticValidationError) -> ValidationError:
    first_error = exc.errors()[0]
    loc = ".".join(str(p) for p in first_error["loc"])
    msg = first_error["msg"]
    return ValidationError(f"Validation failed at '{loc}': {msg}", field_location=loc)


# --- Theme ---

def theme_to_dto(schema: ThemeSchema) -> ThemeDTO:
    return ThemeDTO(
        bg_primary=schema.bg_primary,
        accent_primary=schema.accent_primary,
        accent_secondary=schema.accent_secondary,
        text_primary=schema.text_primary,
    )


def theme_to_schema(dto: ThemeDTO) -> ThemeSchema:
    return ThemeSchema(
        bg_primary=dto.bg_primary,
        accent_primary=dto.accent_primary,
        accent_secondary=dto.accent_secondary,
        text_primary=dto.text_primary,
    )


# --- Scene ---

def scene_to_dto(schema: SceneSchema) -> SceneDTO:
    return SceneDTO(
        id=schema.id,
        narration=schema.narration,
        on_screen_title=schema.on_screen_title,
        visual_intent=schema.visual_intent,
        template=schema.template,
        template_parameters=dict(schema.template_parameters),
        animation_preset=schema.animation_preset,
        sound_effect=schema.sound_effect,
        illustration=schema.illustration,
        narration_audio=schema.narration_audio,
    )


def scene_to_schema(dto: SceneDTO) -> SceneSchema:
    return SceneSchema(
        id=dto.id,
        narration=dto.narration,
        on_screen_title=dto.on_screen_title,
        visual_intent=dto.visual_intent,
        template=dto.template,
        template_parameters=dict(dto.template_parameters),
        animation_preset=dto.animation_preset,
        sound_effect=dto.sound_effect,
        illustration=dto.illustration,
        narration_audio=dto.narration_audio,
    )


# --- Storyboard ---

def parse_storyboard(json_str: str) -> StoryboardDTO:
    try:
        data = json.loads(json_str)
        schema = StoryboardSchema.model_validate(data)
        return StoryboardDTO(
            schema_version=schema.schema_version,
            topic=schema.topic,
            project_title=schema.project_title,
            locale=schema.locale,
            duration_target=schema.duration_target,
            theme=theme_to_dto(schema.theme),
            scenes=tuple(scene_to_dto(s) for s in schema.scenes),
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON format: {exc}") from exc
    except PydanticValidationError as exc:
        raise _format_pydantic_error(exc) from exc


def serialize_storyboard(dto: StoryboardDTO) -> str:
    schema = StoryboardSchema(
        schema_version=dto.schema_version,
        topic=dto.topic,
        project_title=dto.project_title,
        locale=dto.locale,
        duration_target=dto.duration_target,
        theme=theme_to_schema(dto.theme),
        scenes=[scene_to_schema(s) for s in dto.scenes],
    )
    return schema.model_dump_json(by_alias=True, indent=2)


# --- Prepared Scene & Manifest ---

def prepared_scene_to_dto(schema: PreparedSceneSchema) -> PreparedSceneDTO:
    return PreparedSceneDTO(
        id=schema.id,
        narration=schema.narration,
        on_screen_title=schema.on_screen_title,
        template=schema.template,
        template_parameters=dict(schema.template_parameters),
        animation_preset=schema.animation_preset,
        sound_effect=schema.sound_effect,
        audio_file=schema.audio_file,
        audio_digest=schema.audio_digest,
        measured_audio_duration=schema.measured_audio_duration,
        start_frame=schema.start_frame,
        audio_frame_count=schema.audio_frame_count,
        scene_frame_count=schema.scene_frame_count,
        trailing_pause_frames=schema.trailing_pause_frames,
        illustration_file=schema.illustration_file,
        illustration_digest=schema.illustration_digest,
    )


def prepared_scene_to_schema(dto: PreparedSceneDTO) -> PreparedSceneSchema:
    return PreparedSceneSchema(
        id=dto.id,
        narration=dto.narration,
        on_screen_title=dto.on_screen_title,
        template=dto.template,
        template_parameters=dict(dto.template_parameters),
        animation_preset=dto.animation_preset,
        sound_effect=dto.sound_effect,
        audio_file=dto.audio_file,
        audio_digest=dto.audio_digest,
        measured_audio_duration=dto.measured_audio_duration,
        start_frame=dto.start_frame,
        audio_frame_count=dto.audio_frame_count,
        scene_frame_count=dto.scene_frame_count,
        trailing_pause_frames=dto.trailing_pause_frames,
        illustration_file=dto.illustration_file,
        illustration_digest=dto.illustration_digest,
    )


def asset_to_dto(schema: AssetRecordSchema) -> AssetRecordDTO:
    return AssetRecordDTO(
        path=schema.path,
        digest=schema.digest,
        media_type=schema.media_type,
        provenance=schema.provenance,
        attribution=schema.attribution,
    )


def asset_to_schema(dto: AssetRecordDTO) -> AssetRecordSchema:
    return AssetRecordSchema(
        path=dto.path,
        digest=dto.digest,
        media_type=dto.media_type,
        provenance=dto.provenance,
        attribution=dto.attribution,
    )


def parse_manifest(json_str: str) -> RenderManifestDTO:
    try:
        data = json.loads(json_str)
        schema = RenderManifestSchema.model_validate(data)
        return RenderManifestDTO(
            schema_version=schema.schema_version,
            run_id=schema.run_id,
            input_digest=schema.input_digest,
            template_version=schema.template_version,
            render_seed=schema.render_seed,
            fps=schema.fps,
            total_frame_count=schema.total_frame_count,
            scenes=tuple(prepared_scene_to_dto(s) for s in schema.scenes),
            assets=tuple(asset_to_dto(a) for a in schema.assets),
            theme=theme_to_dto(schema.theme),
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON format: {exc}") from exc
    except PydanticValidationError as exc:
        raise _format_pydantic_error(exc) from exc


def serialize_manifest(dto: RenderManifestDTO) -> str:
    schema = RenderManifestSchema(
        schema_version=dto.schema_version,
        run_id=dto.run_id,
        input_digest=dto.input_digest,
        template_version=dto.template_version,
        render_seed=dto.render_seed,
        fps=dto.fps,
        total_frame_count=dto.total_frame_count,
        scenes=[prepared_scene_to_schema(s) for s in dto.scenes],
        assets=[asset_to_schema(a) for a in dto.assets],
        theme=theme_to_schema(dto.theme),
    )
    return schema.model_dump_json(by_alias=True, indent=2)


# --- Run Report ---

def parse_report(json_str: str) -> RunReportDTO:
    try:
        data = json.loads(json_str)
        schema = RunReportSchema.model_validate(data)
        return RunReportDTO(
            run_id=schema.run_id,
            operation=schema.operation,
            status=schema.status,
            input_digest=schema.input_digest,
            stages=tuple(
                RunStageDTO(
                    name=s.name,
                    status=s.status,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    error_message=s.error_message,
                )
                for s in schema.stages
            ),
            outputs=tuple(
                OutputMediaMetadataDTO(
                    path=o.path,
                    orientation=o.orientation,
                    width=o.width,
                    height=o.height,
                    fps=o.fps,
                    duration_seconds=o.duration_seconds,
                    total_frames=o.total_frames,
                    video_codec=o.video_codec,
                    pixel_format=o.pixel_format,
                    audio_codec=o.audio_codec,
                    audio_sample_rate=o.audio_sample_rate,
                    file_size_bytes=o.file_size_bytes,
                )
                for o in schema.outputs
            ),
            warnings=tuple(schema.warnings),
            asset_credits=tuple(schema.asset_credits),
            created_at=schema.created_at,
            updated_at=schema.updated_at,
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON format: {exc}") from exc
    except PydanticValidationError as exc:
        raise _format_pydantic_error(exc) from exc


def serialize_report(dto: RunReportDTO) -> str:
    schema = RunReportSchema(
        run_id=dto.run_id,
        operation=dto.operation,
        status=dto.status,
        input_digest=dto.input_digest,
        stages=[
            RunStageSchema(
                name=s.name,
                status=s.status,
                started_at=s.started_at,
                completed_at=s.completed_at,
                error_message=s.error_message,
            )
            for s in dto.stages
        ],
        outputs=[
            OutputMediaMetadataSchema(
                path=o.path,
                orientation=o.orientation,
                width=o.width,
                height=o.height,
                fps=o.fps,
                duration_seconds=o.duration_seconds,
                total_frames=o.total_frames,
                video_codec=o.video_codec,
                pixel_format=o.pixel_format,
                audio_codec=o.audio_codec,
                audio_sample_rate=o.audio_sample_rate,
                file_size_bytes=o.file_size_bytes,
            )
            for o in dto.outputs
        ],
        warnings=list(dto.warnings),
        asset_credits=list(dto.asset_credits),
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )
    return schema.model_dump_json(by_alias=True, indent=2)

"""Tests for Pydantic serialization and validation adapter."""

import pytest
from space_motion_studio.adapters.serialization.mapper import (
    parse_manifest,
    parse_report,
    parse_storyboard,
    serialize_manifest,
    serialize_report,
    serialize_storyboard,
)
from space_motion_studio.application.dtos import (
    AssetRecordDTO,
    PreparedSceneDTO,
    RenderManifestDTO,
    SceneDTO,
    StoryboardDTO,
    ThemeDTO,
)
from space_motion_studio.domain.errors import ValidationError


def test_storyboard_roundtrip_and_camelcase():
    dto = StoryboardDTO(
        schema_version="1.0.0",
        topic="Black Holes",
        project_title="رحلة إلى الثقب الأسود",
        locale="ar-EG",
        duration_target=7.0,
        theme=ThemeDTO(
            bg_primary="#050713",
            accent_primary="#38bdf8",
            accent_secondary="#f59e0b",
            text_primary="#ffffff",
        ),
        scenes=(
            SceneDTO(
                id="scene-01",
                narration="الثقب الأسود",
                on_screen_title="ما هو الثقب الأسود؟",
                visual_intent="A glowing black hole",
                template="title-illustration",
                template_parameters={"scale": 1.0},
                animation_preset="zoom-in",
                sound_effect="whoosh",
                illustration="assets/illustrations/black_hole.svg",
                narration_audio="assets/audio/black_hole.mp3",
            ),
        ),
    )

    serialized = serialize_storyboard(dto)
    assert '"schemaVersion": "1.0.0"' in serialized
    assert '"onScreenTitle": "ما هو الثقب الأسود؟"' in serialized
    assert '"visualIntent": "A glowing black hole"' in serialized
    assert '"animationPreset": "zoom-in"' in serialized
    assert '"soundEffect": "whoosh"' in serialized

    # Parse back
    parsed = parse_storyboard(serialized)
    assert parsed.schema_version == "1.0.0"
    assert parsed.project_title == "رحلة إلى الثقب الأسود"
    assert len(parsed.scenes) == 1
    assert parsed.scenes[0].id == "scene-01"


def test_forbid_unknown_fields_in_storyboard():
    raw_json = """{
        "schemaVersion": "1.0.0",
        "topic": "Space",
        "projectTitle": "Title",
        "locale": "ar-EG",
        "durationTarget": 5.0,
        "theme": {
            "bgPrimary": "#000000",
            "accentPrimary": "#111111",
            "accentSecondary": "#222222",
            "textPrimary": "#ffffff"
        },
        "scenes": [
            {
                "id": "s1",
                "narration": "Text",
                "onScreenTitle": "Title",
                "visualIntent": "Intent",
                "template": "title-illustration",
                "templateParameters": {},
                "animationPreset": "zoom-in",
                "soundEffect": "whoosh"
            }
        ],
        "rogueProperty": "not allowed"
    }"""
    with pytest.raises(ValidationError) as exc_info:
        parse_storyboard(raw_json)
    assert "rogueProperty" in str(exc_info.value) or "extra" in str(exc_info.value)


def test_manifest_roundtrip():
    dto = RenderManifestDTO(
        schema_version="1.0.0",
        run_id="run-123",
        input_digest="sha256:abcd",
        template_version="1.0.0",
        render_seed=42,
        fps=30,
        total_frame_count=214,
        scenes=(
            PreparedSceneDTO(
                id="s1",
                narration="text",
                on_screen_title="title",
                template="title-illustration",
                template_parameters={},
                animation_preset="zoom-in",
                sound_effect="whoosh",
                audio_file="assets/audio/s1.mp3",
                audio_digest="sha256:1234",
                measured_audio_duration=6.72,
                start_frame=0,
                audio_frame_count=202,
                scene_frame_count=214,
                trailing_pause_frames=12,
                illustration_file="assets/illustrations/s1.svg",
                illustration_digest="sha256:5678",
            ),
        ),
        assets=(
            AssetRecordDTO(
                path="assets/audio/s1.mp3",
                digest="sha256:1234",
                media_type="audio/mp3",
                provenance="bundled/audio/intro.mp3",
                attribution="Bundled voice",
            ),
        ),
        theme=ThemeDTO(),
    )

    serialized = serialize_manifest(dto)
    assert '"schemaVersion": "1.0.0"' in serialized
    assert '"runId": "run-123"' in serialized
    assert '"totalFrameCount": 214' in serialized

    parsed = parse_manifest(serialized)
    assert parsed.run_id == "run-123"
    assert parsed.total_frame_count == 214
    assert len(parsed.scenes) == 1
    assert parsed.scenes[0].audio_frame_count == 202

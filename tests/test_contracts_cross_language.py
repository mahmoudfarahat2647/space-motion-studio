"""Cross-language interchange contract test.

Serializes Python DTOs to JSON and validates them with the production TypeScript
Zod parser using pnpm.
"""

import json
import os
import subprocess
import tempfile
import pytest
from space_motion_studio.adapters.preflight.diagnostics import resolve_executable
from space_motion_studio.adapters.serialization.mapper import (
    serialize_manifest,
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


@pytest.fixture(scope="module")
def pnpm_exe():
    exe = resolve_executable("pnpm")
    assert exe is not None, "pnpm must be available on PATH"
    return exe


def run_ts_validator(pnpm_exe: str, contract_type: str, json_content: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write(json_content)
        path = f.name

    try:
        cmd = [
            pnpm_exe,
            "exec",
            "tsx",
            "src/scripts/validate-manifest.ts",
            contract_type,
            path,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_cross_language_valid_storyboard(pnpm_exe):
    dto = StoryboardDTO(
        schema_version="1.0.0",
        topic="Cross Language Test",
        project_title="اختبار عبر اللغات",
        locale="ar-EG",
        duration_target=10.0,
        theme=ThemeDTO(),
        scenes=(
            SceneDTO(
                id="scene-01",
                narration="نص تجريبي للتحقق من التوافق",
                on_screen_title="عنوان تجريبي",
                visual_intent="A futuristic space station",
                template="title-illustration",
                template_parameters={"zoom": 1.2},
                animation_preset="zoom-in",
                sound_effect="whoosh",
                illustration="assets/illustrations/station.svg",
                narration_audio="assets/audio/station.mp3",
            ),
        ),
    )
    serialized = serialize_storyboard(dto)
    result = run_ts_validator(pnpm_exe, "storyboard", serialized)
    assert result.returncode == 0, f"TypeScript parser rejected valid Python storyboard: {result.stderr}"


def test_cross_language_valid_manifest(pnpm_exe):
    dto = RenderManifestDTO(
        schema_version="1.0.0",
        run_id="run-cross-lang-01",
        input_digest="sha256:11223344",
        template_version="1.0.0",
        render_seed=42,
        fps=30,
        total_frame_count=214,
        scenes=(
            PreparedSceneDTO(
                id="scene-01",
                narration="نص عربي",
                on_screen_title="عنوان عربي",
                template="title-illustration",
                template_parameters={"zoom": 1.0},
                animation_preset="zoom-in",
                sound_effect="whoosh",
                audio_file="assets/audio/scene-01.mp3",
                audio_digest="sha256:aabbcc",
                measured_audio_duration=6.72,
                start_frame=0,
                audio_frame_count=202,
                scene_frame_count=214,
                trailing_pause_frames=12,
                illustration_file="assets/illustrations/scene-01.svg",
                illustration_digest="sha256:ddeeff",
            ),
        ),
        assets=(
            AssetRecordDTO(
                path="assets/audio/scene-01.mp3",
                digest="sha256:aabbcc",
                media_type="audio/mp3",
                provenance="bundled/audio/intro.mp3",
                attribution="Bundled Arabic Voice",
            ),
        ),
        theme=ThemeDTO(),
    )
    serialized = serialize_manifest(dto)
    result = run_ts_validator(pnpm_exe, "manifest", serialized)
    assert result.returncode == 0, f"TypeScript parser rejected valid Python manifest: {result.stderr}"


def test_cross_language_rejects_unknown_fields(pnpm_exe):
    dto = StoryboardDTO(
        schema_version="1.0.0",
        topic="Cross Language Test",
        project_title="عنوان",
        locale="ar-EG",
        duration_target=5.0,
        theme=ThemeDTO(),
        scenes=(
            SceneDTO(
                id="s1",
                narration="n",
                on_screen_title="t",
                visual_intent="v",
                template="title-illustration",
                template_parameters={},
                animation_preset="zoom-in",
                sound_effect="whoosh",
            ),
        ),
    )
    data = json.loads(serialize_storyboard(dto))
    data["unknownExtraKey"] = "rejected"
    tampered_json = json.dumps(data)

    result = run_ts_validator(pnpm_exe, "storyboard", tampered_json)
    assert result.returncode != 0
    assert "unknownExtraKey" in result.stderr or "unrecognized_keys" in result.stderr

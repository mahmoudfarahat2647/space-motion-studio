"""Composition root for Space Motion Studio.

Wires together concrete adapters with application use cases according to
the Dependency Inversion Principle (DIP).
"""

import json
import os
from space_motion_studio.adapters.media.ffprobe_inspector import FFprobeInspector
from space_motion_studio.adapters.preflight.diagnostics import SystemPreflightAdapter
from space_motion_studio.adapters.rendering.remotion_renderer import RemotionRenderer
from space_motion_studio.adapters.serialization.mapper import (
    parse_storyboard,
    serialize_manifest,
    serialize_report,
    serialize_storyboard,
)
from space_motion_studio.adapters.storage.fs_storage import FileSystemRunStorage
from space_motion_studio.application.dtos import StoryboardDTO
from space_motion_studio.application.use_cases.compile_timeline import CompileTimelineUseCase
from space_motion_studio.application.use_cases.prepare_run import PrepareRunUseCase
from space_motion_studio.application.use_cases.produce_demo import ProduceDemoUseCase
from space_motion_studio.application.use_cases.render_video import RenderVideoUseCase


def get_bundled_dir() -> str:
    """Return absolute path to bundled demo assets."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bundled"))


def get_bundled_font_path() -> str:
    """Return absolute path to bundled Cairo font."""
    return os.path.join(get_bundled_dir(), "fonts", "Cairo.ttf")


def load_bundled_demo_storyboard() -> tuple[StoryboardDTO, str]:
    """Load the bundled single-scene demo storyboard with resolved asset paths."""
    bundled_dir = get_bundled_dir()
    storyboard_path = os.path.join(bundled_dir, "demo_storyboard.json")

    with open(storyboard_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Resolve relative asset paths in bundled directory
    for scene in data.get("scenes", []):
        if scene.get("narrationAudio"):
            scene["narrationAudio"] = os.path.abspath(
                os.path.join(bundled_dir, scene["narrationAudio"])
            )
        if scene.get("illustration"):
            scene["illustration"] = os.path.abspath(
                os.path.join(bundled_dir, scene["illustration"])
            )

    resolved_json = json.dumps(data, ensure_ascii=False, indent=2)
    dto = parse_storyboard(resolved_json)
    return dto, resolved_json


def build_produce_demo_use_case(
    workspace_root: str | None = None,
    runs_dir: str = "runs",
) -> ProduceDemoUseCase:
    """Compose and return the ProduceDemoUseCase with production adapters."""
    ws = os.path.abspath(workspace_root or os.getcwd())
    storage = FileSystemRunStorage(base_runs_dir=os.path.join(ws, runs_dir))
    inspector = FFprobeInspector()
    preflight = SystemPreflightAdapter(workspace_root=ws)
    renderer = RemotionRenderer(workspace_root=ws)
    timeline_compiler = CompileTimelineUseCase()

    prepare_uc = PrepareRunUseCase(
        storage=storage,
        audio_inspector=inspector,
        timeline_compiler=timeline_compiler,
        serialize_manifest=serialize_manifest,
    )

    render_uc = RenderVideoUseCase(
        storage=storage,
        renderer=renderer,
        inspector=inspector,
    )

    return ProduceDemoUseCase(
        storage=storage,
        preflight=preflight,
        prepare_run_uc=prepare_uc,
        render_video_uc=render_uc,
        load_demo_storyboard=load_bundled_demo_storyboard,
        get_bundled_font_path=get_bundled_font_path,
        serialize_report=serialize_report,
        serialize_manifest=serialize_manifest,
    )

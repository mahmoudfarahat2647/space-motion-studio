"""Produce demo use case.

Coordinates end-to-end demo production without requiring external API credentials.
Follows Clean Architecture: no direct filesystem (os.path) operations in application layer.
"""

from datetime import datetime, timezone
import uuid
from typing import Callable
from space_motion_studio.application.dtos import (
    AssetRecordDTO,
    OutputMediaMetadataDTO,
    RenderManifestDTO,
    RunReportDTO,
    RunStageDTO,
    StoryboardDTO,
)
from space_motion_studio.application.ports.preflight import PreflightPort
from space_motion_studio.application.ports.run_storage import RunStoragePort
from space_motion_studio.application.use_cases.prepare_run import PrepareRunUseCase
from space_motion_studio.application.use_cases.render_video import RenderVideoUseCase
from space_motion_studio.domain.errors import PreflightError


class ProduceDemoUseCase:
    """Executes the public demo production pipeline."""

    def __init__(
        self,
        storage: RunStoragePort,
        preflight: PreflightPort,
        prepare_run_uc: PrepareRunUseCase,
        render_video_uc: RenderVideoUseCase,
        load_demo_storyboard: Callable[[], tuple[StoryboardDTO, str]],
        get_bundled_font_path: Callable[[], str],
        serialize_report: Callable[[RunReportDTO], str],
        serialize_manifest: Callable[[RenderManifestDTO], str],
    ) -> None:
        self._storage = storage
        self._preflight = preflight
        self._prepare_run_uc = prepare_run_uc
        self._render_video_uc = render_video_uc
        self._load_demo_storyboard = load_demo_storyboard
        self._get_bundled_font_path = get_bundled_font_path
        self._serialize_report = serialize_report
        self._serialize_manifest = serialize_manifest

    def execute(self, run_id: str | None = None) -> RunReportDTO:
        # 1. Preflight check
        preflight_report = self._preflight.run_diagnostics()
        if not preflight_report.all_passed:
            failed_msgs = [f"{c.name}: {c.message}" for c in preflight_report.checks if not c.passed]
            raise PreflightError("Preflight diagnostics failed:\n" + "\n".join(failed_msgs))

        # 2. Generate run id if not provided
        if not run_id:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            short_id = uuid.uuid4().hex[:8]
            run_id = f"run_{timestamp}_{short_id}"

        # 3. Create run and acquire lock
        self._storage.create_run(run_id)
        self._storage.acquire_lock(run_id)

        stages: list[RunStageDTO] = []
        outputs: list[OutputMediaMetadataDTO] = []
        input_digest = ""
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            # Stage 1: Preparation
            prep_start = datetime.now(timezone.utc).isoformat()
            storyboard, storyboard_json = self._load_demo_storyboard()

            # Copy font asset into run if present
            font_path = self._get_bundled_font_path()
            font_record: AssetRecordDTO | None = None
            if self._storage.file_exists(font_path):
                dest_font_rel = "assets/fonts/Cairo.ttf"
                _, font_digest = self._storage.copy_asset_to_run(run_id, font_path, dest_font_rel)
                font_record = AssetRecordDTO(
                    path=dest_font_rel,
                    digest=font_digest,
                    media_type="font/ttf",
                    provenance=font_path,
                    attribution="Cairo Font (SIL Open Font License)",
                )

            manifest = self._prepare_run_uc.execute(
                run_id=run_id,
                storyboard=storyboard,
                storyboard_json=storyboard_json,
            )
            input_digest = manifest.input_digest

            # If font was copied, ensure it is recorded in manifest assets
            if font_record:
                manifest = RenderManifestDTO(
                    schema_version=manifest.schema_version,
                    run_id=manifest.run_id,
                    input_digest=manifest.input_digest,
                    template_version=manifest.template_version,
                    render_seed=manifest.render_seed,
                    fps=manifest.fps,
                    total_frame_count=manifest.total_frame_count,
                    scenes=manifest.scenes,
                    assets=manifest.assets + (font_record,),
                    theme=manifest.theme,
                )
            manifest_json = self._serialize_manifest(manifest)
            manifest_file_path = self._storage.save_manifest(run_id, manifest_json)

            stages.append(
                RunStageDTO(
                    name="prepare",
                    status="completed",
                    started_at=prep_start,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
            )

            # Stage 2: Render
            render_start = datetime.now(timezone.utc).isoformat()
            metadata = self._render_video_uc.execute(
                manifest=manifest,
                manifest_file_path=manifest_file_path,
                orientation="landscape",
                width=1920,
                height=1080,
            )
            outputs.append(metadata)

            stages.append(
                RunStageDTO(
                    name="render",
                    status="completed",
                    started_at=render_start,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )
            )

            # 4. Success report
            report = RunReportDTO(
                run_id=run_id,
                operation="produce_demo",
                status="completed",
                input_digest=input_digest,
                stages=tuple(stages),
                outputs=tuple(outputs),
                warnings=(),
                asset_credits=(
                    "Bundled Arabic narration (ar-EG)",
                    "Local Black Hole vector illustration",
                    "Cairo font (SIL Open Font License)",
                ),
                created_at=now_iso,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            report_json = self._serialize_report(report)
            self._storage.save_report(run_id, report_json)
            return report

        except Exception as exc:
            stages.append(
                RunStageDTO(
                    name="error",
                    status="failed",
                    started_at=now_iso,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    error_message=str(exc),
                )
            )
            failed_report = RunReportDTO(
                run_id=run_id,
                operation="produce_demo",
                status="failed",
                input_digest=input_digest,
                stages=tuple(stages),
                outputs=tuple(outputs),
                warnings=(),
                asset_credits=(),
                created_at=now_iso,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                report_json = self._serialize_report(failed_report)
                self._storage.save_report(run_id, report_json)
            except Exception:
                pass
            raise

        finally:
            self._storage.release_lock(run_id)

"""Acceptance tests for the public demo production workflow and CLI.

Exercises the public command with a real short render, inspects output streams
and frame count, verifies isolation, CLI invocation, paths with spaces,
and asset digest integrity.
"""

import os
import subprocess
import sys
import tempfile
import pytest
from space_motion_studio.adapters.media.ffprobe_inspector import FFprobeInspector
from space_motion_studio.adapters.storage.fs_storage import compute_sha256
from space_motion_studio.domain.errors import ResourceNotFoundError
from space_motion_studio.entrypoints import cli
from space_motion_studio.entrypoints.composition_root import build_produce_demo_use_case


def test_public_demo_production_end_to_end():
    """Exercise production through the composed use case."""
    with tempfile.TemporaryDirectory() as tmp_runs_dir:
        use_case = build_produce_demo_use_case(runs_dir=tmp_runs_dir)

        run_id = "test-demo-acceptance-run"
        report = use_case.execute(run_id=run_id)

        # 1. Assert overall run status and report
        assert report.run_id == run_id
        assert report.status == "completed"
        assert report.input_digest.startswith("sha256:")
        assert len(report.stages) == 2
        assert [s.name for s in report.stages] == ["prepare", "render"]
        assert all(s.status == "completed" for s in report.stages)

        # 2. Assert output metadata
        assert len(report.outputs) == 1
        output = report.outputs[0]
        assert output.orientation == "landscape"
        assert output.width == 1920
        assert output.height == 1080
        assert abs(output.fps - 30.0) < 0.05
        assert output.total_frames == 214
        assert "h264" in output.video_codec.lower()
        assert output.pixel_format.lower() in ("yuv420p", "yuvj420p")
        assert "aac" in output.audio_codec.lower()
        assert output.audio_sample_rate == 48000
        assert os.path.exists(output.path)
        assert os.path.getsize(output.path) > 10000

        # 3. Independent inspection using FFprobeInspector
        inspector = FFprobeInspector()
        verified_meta = inspector.inspect_video(output.path, orientation="landscape")
        assert verified_meta.width == 1920
        assert verified_meta.height == 1080
        assert abs(verified_meta.fps - 30.0) < 0.05
        assert verified_meta.total_frames == 214
        assert "h264" in verified_meta.video_codec.lower()
        assert "aac" in verified_meta.audio_codec.lower()
        assert verified_meta.audio_sample_rate == 48000

        # 4. Assert isolated run files exist
        run_dir = os.path.join(tmp_runs_dir, run_id)
        assert os.path.exists(os.path.join(run_dir, "storyboard.json"))
        assert os.path.exists(os.path.join(run_dir, "manifest.json"))
        assert os.path.exists(os.path.join(run_dir, "report.json"))
        # Ensure lock was cleanly released
        assert not os.path.exists(os.path.join(run_dir, ".lock"))


def test_public_cli_preflight_command():
    """Exercise the public CLI preflight command via subprocess."""
    cmd = [sys.executable, "-m", "space_motion_studio", "preflight"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert res.returncode == 0
    assert "Preflight Diagnostics" in res.stdout
    assert "Preflight check PASSED" in res.stdout


def test_public_cli_module_execution():
    """Exercise the public CLI entrypoint via python -m space_motion_studio demo."""
    with tempfile.TemporaryDirectory() as tmp_runs_dir:
        run_id = "test-cli-run"
        cmd = [
            sys.executable,
            "-m",
            "space_motion_studio",
            "demo",
            "--run-id",
            run_id,
            "--runs-dir",
            tmp_runs_dir,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert res.returncode == 0, f"CLI command failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        assert "Production COMPLETED successfully!" in res.stdout

        # Verify export artifact was created and matches all criteria
        export_path = os.path.join(tmp_runs_dir, run_id, "exports", "landscape.mp4")
        assert os.path.exists(export_path)
        assert os.path.getsize(export_path) > 10000

        inspector = FFprobeInspector()
        meta = inspector.inspect_video(export_path)
        assert meta.width == 1920
        assert meta.height == 1080
        assert meta.total_frames == 214
        assert "h264" in meta.video_codec.lower()
        assert "aac" in meta.audio_codec.lower()
        assert meta.audio_sample_rate == 48000


def test_paths_with_spaces_support():
    """Verify that runs directory containing spaces is handled correctly by renderer and CLI."""
    with tempfile.TemporaryDirectory(prefix="space motion run dir ") as tmp_runs_dir:
        run_id = "run with spaces 01"
        exit_code = cli.main([
            "demo",
            "--run-id",
            run_id,
            "--runs-dir",
            tmp_runs_dir,
        ])
        assert exit_code == 0

        export_path = os.path.join(tmp_runs_dir, run_id, "exports", "landscape.mp4")
        assert os.path.exists(export_path)
        assert os.path.getsize(export_path) > 10000

        # Verify ffprobe can inspect path with spaces
        inspector = FFprobeInspector()
        meta = inspector.inspect_video(export_path)
        assert meta.total_frames == 214


def test_tampered_asset_integrity_rejection():
    """Verify that if an asset digest is modified/corrupted, rendering is rejected."""
    with tempfile.TemporaryDirectory() as tmp_runs_dir:
        use_case = build_produce_demo_use_case(runs_dir=tmp_runs_dir)
        run_id = "test-tamper-run"

        # First stage: prepare run
        storyboard, sb_json = use_case._load_demo_storyboard()
        manifest = use_case._prepare_run_uc.execute(
            run_id=run_id,
            storyboard=storyboard,
            storyboard_json=sb_json,
        )

        # Tamper with the audio asset file on disk
        audio_file_path = os.path.join(use_case._storage.get_run_dir(run_id), manifest.scenes[0].audio_file)
        with open(audio_file_path, "wb") as f:
            f.write(b"tampered audio data")

        # Now attempting to render must fail due to digest mismatch
        with pytest.raises(ResourceNotFoundError):
            use_case._render_video_uc.execute(
                manifest=manifest,
                manifest_file_path=os.path.join(use_case._storage.get_run_dir(run_id), "manifest.json"),
                orientation="landscape",
            )

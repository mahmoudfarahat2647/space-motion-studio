"""Remotion CLI renderer adapter.

Implements VideoRendererPort by invoking the pinned Remotion CLI via pnpm.
Handles Windows executable resolution, paths with spaces, and parameter passing.
"""

import os
import subprocess
from space_motion_studio.adapters.preflight.diagnostics import resolve_executable
from space_motion_studio.application.ports.video_renderer import VideoRendererPort
from space_motion_studio.domain.errors import RenderError, ResourceNotFoundError


class RemotionRenderer(VideoRendererPort):
    """Renders video using Remotion CLI via pnpm."""

    def __init__(
        self,
        workspace_root: str | None = None,
        entry_point: str = "src/index.ts",
        concurrency: int | None = None,
    ) -> None:
        self.workspace_root = os.path.abspath(workspace_root or os.getcwd())
        self.entry_point = entry_point
        self.concurrency = concurrency
        self._pnpm_exe = resolve_executable("pnpm")
        if not self._pnpm_exe:
            raise ResourceNotFoundError(
                "pnpm executable not found on PATH. Remotion operations strictly require pnpm."
            )

    def render(
        self,
        manifest_path: str,
        public_dir: str,
        output_path: str,
        orientation: str = "landscape",
        fps: int = 30,
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        composition_id = "MainLandscape" if orientation.lower() == "landscape" else "MainVertical"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Build command array (avoids shell quoting issues with spaces)
        cmd = [
            self._pnpm_exe,
            "exec",
            "remotion",
            "render",
            self.entry_point,
            composition_id,
            f"--output={os.path.abspath(output_path)}",
            f"--props={os.path.abspath(manifest_path)}",
            f"--public-dir={os.path.abspath(public_dir)}",
            f"--width={width}",
            f"--height={height}",
            f"--fps={fps}",
            "--image-format=png",
            "--codec=h264",
            "--pixel-format=yuv420p",
            "--audio-codec=aac",
            "--sample-rate=48000",
            "--enforce-audio-track",
            "--overwrite",
        ]

        if self.concurrency and self.concurrency > 0:
            cmd.append(f"--concurrency={self.concurrency}")

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or ""
            stdout = exc.stdout or ""
            raise RenderError(
                f"Remotion render failed with exit code {exc.returncode}.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            ) from exc

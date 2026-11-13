"""Preflight dependency diagnostics adapter.

Checks Python, Node, pnpm, ffmpeg, ffprobe, and Remotion browser executable.
"""

import os
import shutil
import subprocess
import sys
from space_motion_studio.application.dtos import PreflightCheckDTO, PreflightReportDTO
from space_motion_studio.application.ports.preflight import PreflightPort


def resolve_executable(name: str) -> str | None:
    """Resolve an executable on Windows or Unix systems."""
    exe = shutil.which(name)
    if exe:
        return exe
    # On Windows, try with .cmd and .exe extensions
    for ext in (".cmd", ".exe", ".bat"):
        candidate = shutil.which(f"{name}{ext}")
        if candidate:
            return candidate
    return None


class SystemPreflightAdapter(PreflightPort):
    """Checks required system and toolchain dependencies."""

    def __init__(self, workspace_root: str | None = None) -> None:
        self.workspace_root = os.path.abspath(workspace_root or os.getcwd())

    def _check_python(self) -> PreflightCheckDTO:
        major, minor = sys.version_info.major, sys.version_info.minor
        version_str = f"{major}.{minor}.{sys.version_info.micro}"
        passed = (major == 3 and minor >= 10)
        msg = f"Python {version_str} found" if passed else f"Python >= 3.10 required, got {version_str}"
        return PreflightCheckDTO(name="Python", passed=passed, version=version_str, message=msg)

    def _check_node(self) -> PreflightCheckDTO:
        exe = resolve_executable("node")
        if not exe:
            return PreflightCheckDTO(name="Node.js", passed=False, version=None, message="Node.js executable not found on PATH")
        try:
            res = subprocess.run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            version = res.stdout.strip()
            passed = version.startswith("v") and int(version[1:].split(".")[0]) >= 18
            return PreflightCheckDTO(name="Node.js", passed=passed, version=version, message=f"Node.js {version} found")
        except Exception as e:
            return PreflightCheckDTO(name="Node.js", passed=False, version=None, message=f"Failed to check Node: {e}")

    def _check_pnpm(self) -> PreflightCheckDTO:
        exe = resolve_executable("pnpm")
        if not exe:
            return PreflightCheckDTO(name="pnpm", passed=False, version=None, message="pnpm executable not found on PATH. Remotion operations strictly require pnpm.")
        try:
            res = subprocess.run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            version = res.stdout.strip()
            return PreflightCheckDTO(name="pnpm", passed=True, version=version, message=f"pnpm {version} found at {exe}")
        except Exception as e:
            return PreflightCheckDTO(name="pnpm", passed=False, version=None, message=f"Failed to check pnpm: {e}")

    def _check_ffmpeg(self) -> PreflightCheckDTO:
        exe = resolve_executable("ffmpeg")
        if not exe:
            return PreflightCheckDTO(name="FFmpeg", passed=False, version=None, message="ffmpeg executable not found on PATH")
        try:
            res = subprocess.run([exe, "-version"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            first_line = res.stdout.splitlines()[0] if res.stdout else "unknown"
            return PreflightCheckDTO(name="FFmpeg", passed=True, version=first_line, message=f"FFmpeg found: {first_line}")
        except Exception as e:
            return PreflightCheckDTO(name="FFmpeg", passed=False, version=None, message=f"Failed to check FFmpeg: {e}")

    def _check_ffprobe(self) -> PreflightCheckDTO:
        exe = resolve_executable("ffprobe")
        if not exe:
            return PreflightCheckDTO(name="FFprobe", passed=False, version=None, message="ffprobe executable not found on PATH")
        try:
            res = subprocess.run([exe, "-version"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            first_line = res.stdout.splitlines()[0] if res.stdout else "unknown"
            return PreflightCheckDTO(name="FFprobe", passed=True, version=first_line, message=f"FFprobe found: {first_line}")
        except Exception as e:
            return PreflightCheckDTO(name="FFprobe", passed=False, version=None, message=f"Failed to check FFprobe: {e}")

    def _check_browser(self) -> PreflightCheckDTO:
        # Check Remotion's provisioned headless shell
        remotion_shell = os.path.join(
            self.workspace_root,
            "node_modules",
            ".remotion",
            "chrome-headless-shell",
            "win64",
            "chrome-headless-shell-win64",
            "chrome-headless-shell.exe",
        )
        if os.path.exists(remotion_shell):
            return PreflightCheckDTO(
                name="Browser",
                passed=True,
                version="Remotion Chrome Headless Shell",
                message=f"Provisioned Chrome Headless Shell found at {remotion_shell}",
            )
        # Check standard Google Chrome
        chrome_exe = resolve_executable("chrome")
        if not chrome_exe:
            for cand in (
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ):
                if os.path.exists(cand):
                    chrome_exe = cand
                    break
        if chrome_exe:
            return PreflightCheckDTO(
                name="Browser",
                passed=True,
                version="System Browser",
                message=f"System browser found at {chrome_exe}",
            )
        return PreflightCheckDTO(
            name="Browser",
            passed=False,
            version=None,
            message="No suitable browser found for Remotion rendering. Run 'pnpm exec remotion browser ensure'.",
        )

    def run_diagnostics(self) -> PreflightReportDTO:
        checks = (
            self._check_python(),
            self._check_node(),
            self._check_pnpm(),
            self._check_ffmpeg(),
            self._check_ffprobe(),
            self._check_browser(),
        )
        all_passed = all(c.passed for c in checks)
        return PreflightReportDTO(all_passed=all_passed, checks=checks)

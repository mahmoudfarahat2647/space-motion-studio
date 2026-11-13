"""Preflight dependency diagnostics port."""

from abc import ABC, abstractmethod
from space_motion_studio.application.dtos import PreflightReportDTO


class PreflightPort(ABC):
    """Port for verifying required runtime dependencies (Python, Node, pnpm, FFmpeg, browser)."""

    @abstractmethod
    def run_diagnostics(self) -> PreflightReportDTO:
        """Run system checks and return report."""
        pass

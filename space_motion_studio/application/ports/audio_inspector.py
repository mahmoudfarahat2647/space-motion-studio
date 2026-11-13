"""Audio & media inspection port."""

from abc import ABC, abstractmethod
from space_motion_studio.application.dtos import OutputMediaMetadataDTO


class AudioInspectorPort(ABC):
    """Port for measuring audio and inspecting rendered media."""

    @abstractmethod
    def inspect_audio(self, file_path: str) -> tuple[float, int, int]:
        """Inspect audio file returning (duration_seconds, sample_rate, channels)."""
        pass

    @abstractmethod
    def inspect_video(self, file_path: str, orientation: str) -> OutputMediaMetadataDTO:
        """Inspect rendered video container and streams."""
        pass

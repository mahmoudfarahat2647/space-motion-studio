"""Video renderer port."""

from abc import ABC, abstractmethod


class VideoRendererPort(ABC):
    """Port for rendering video via an external rendering engine (e.g. Remotion)."""

    @abstractmethod
    def render(
        self,
        manifest_path: str,
        public_dir: str,
        output_path: str,
        orientation: str,
        fps: int = 30,
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        """Render video using the specified manifest and parameters."""
        pass

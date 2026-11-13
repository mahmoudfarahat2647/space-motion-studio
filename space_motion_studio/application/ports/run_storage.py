"""Run storage and isolation port."""

from abc import ABC, abstractmethod


class RunStoragePort(ABC):
    """Port for isolated run directory management, locking, snapshots, and atomic promotion."""

    @abstractmethod
    def create_run(self, run_id: str) -> None:
        """Create the run directory structure."""
        pass

    @abstractmethod
    def acquire_lock(self, run_id: str) -> None:
        """Acquire an exclusive lock for the run to prevent concurrent writes."""
        pass

    @abstractmethod
    def release_lock(self, run_id: str) -> None:
        """Release the exclusive lock for the run."""
        pass

    @abstractmethod
    def save_storyboard_snapshot(self, run_id: str, storyboard_json: str) -> tuple[str, str]:
        """Save input storyboard snapshot; returns (path, sha256_digest)."""
        pass

    @abstractmethod
    def copy_asset_to_run(self, run_id: str, source_path: str, relative_dest_path: str) -> tuple[str, str]:
        """Copy asset into run directory; returns (dest_absolute_path, sha256_digest)."""
        pass

    @abstractmethod
    def save_manifest(self, run_id: str, manifest_json: str) -> str:
        """Save render manifest JSON atomically; returns manifest file path."""
        pass

    @abstractmethod
    def save_report(self, run_id: str, report_json: str) -> str:
        """Save run report JSON atomically; returns report file path."""
        pass

    @abstractmethod
    def get_run_dir(self, run_id: str) -> str:
        """Get absolute path to run root directory."""
        pass

    @abstractmethod
    def get_assets_dir(self, run_id: str) -> str:
        """Get absolute path to run assets directory."""
        pass

    @abstractmethod
    def get_exports_dir(self, run_id: str) -> str:
        """Get absolute path to run exports directory."""
        pass

    @abstractmethod
    def get_export_path(self, run_id: str, filename: str) -> str:
        """Get absolute destination path for an export file."""
        pass

    @abstractmethod
    def get_export_temp_path(self, run_id: str, filename: str) -> str:
        """Get absolute temporary staging path for an export file."""
        pass

    @abstractmethod
    def atomic_publish(self, temp_path: str, target_path: str) -> None:
        """Atomically promote a temporary file to target location."""
        pass

    @abstractmethod
    def verify_file_digest(self, file_path: str, expected_digest: str) -> bool:
        """Verify that file exists and matches the expected sha256 digest."""
        pass

    @abstractmethod
    def verify_run_asset(self, run_id: str, relative_path: str, expected_digest: str) -> bool:
        """Verify that a run-relative asset exists and matches the expected sha256 digest."""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check whether a file exists without exposing filesystem details to application."""
        pass

    @abstractmethod
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes without exposing filesystem details to application."""
        pass

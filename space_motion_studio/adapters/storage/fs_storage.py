"""Filesystem run storage adapter.

Implements RunStoragePort with directory isolation, sha256 digests,
atomic publication, and per-run exclusive locks.
"""

import hashlib
import os
import shutil
import tempfile
from space_motion_studio.adapters.storage.run_lock import RunLock
from space_motion_studio.application.ports.run_storage import RunStoragePort


def compute_sha256(file_path: str) -> str:
    """Compute sha256 digest of a file in sha256:<hex> format."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def compute_str_sha256(content: str) -> str:
    """Compute sha256 digest of a string in sha256:<hex> format."""
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


class FileSystemRunStorage(RunStoragePort):
    """Stores run artifacts in an isolated directory structure on disk."""

    def __init__(self, base_runs_dir: str = "runs") -> None:
        self.base_runs_dir = os.path.abspath(base_runs_dir)
        self._locks: dict[str, RunLock] = {}

    def get_run_dir(self, run_id: str) -> str:
        if not run_id or run_id in (".", "..") or "/" in run_id or "\\" in run_id or os.path.isabs(run_id) or ":" in run_id:
            raise ValueError("run ID must be a single directory name")
        return os.path.join(self.base_runs_dir, run_id)

    def get_assets_dir(self, run_id: str) -> str:
        return os.path.join(self.get_run_dir(run_id), "assets")

    def get_exports_dir(self, run_id: str) -> str:
        return os.path.join(self.get_run_dir(run_id), "exports")

    def get_export_path(self, run_id: str, filename: str) -> str:
        return os.path.join(self.get_exports_dir(run_id), filename)

    def get_export_temp_path(self, run_id: str, filename: str) -> str:
        return os.path.join(self.get_exports_dir(run_id), filename)

    def file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def get_file_size(self, file_path: str) -> int:
        return os.path.getsize(file_path)

    def create_run(self, run_id: str) -> None:
        run_dir = self.get_run_dir(run_id)
        os.makedirs(run_dir, exist_ok=True)
        os.makedirs(self.get_assets_dir(run_id), exist_ok=True)
        os.makedirs(self.get_exports_dir(run_id), exist_ok=True)

    def acquire_lock(self, run_id: str) -> None:
        run_dir = self.get_run_dir(run_id)
        lock = RunLock(run_dir=run_dir, run_id=run_id)
        lock.acquire()
        self._locks[run_id] = lock

    def release_lock(self, run_id: str) -> None:
        lock = self._locks.pop(run_id, None)
        if lock:
            lock.release()
        else:
            # Fallback if lock object not cached
            run_dir = self.get_run_dir(run_id)
            fallback_lock = RunLock(run_dir=run_dir, run_id=run_id)
            fallback_lock.release()

    def atomic_publish(self, temp_path: str, target_path: str) -> None:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # On Windows, os.replace replaces existing file atomically
        os.replace(temp_path, target_path)

    def _write_atomic_str(self, target_path: str, content: str) -> None:
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        # Create temp file in same directory for atomic replace
        with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tf:
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())
            temp_name = tf.name
        self.atomic_publish(temp_name, target_path)

    def save_storyboard_snapshot(self, run_id: str, storyboard_json: str) -> tuple[str, str]:
        snapshot_path = os.path.join(self.get_run_dir(run_id), "storyboard.json")
        self._write_atomic_str(snapshot_path, storyboard_json)
        digest = compute_str_sha256(storyboard_json)
        return snapshot_path, digest

    def copy_asset_to_run(self, run_id: str, source_path: str, relative_dest_path: str) -> tuple[str, str]:
        run_dir = self.get_run_dir(run_id)
        target_path = os.path.join(run_dir, relative_dest_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Atomic copy
        target_dir = os.path.dirname(target_path)
        with tempfile.NamedTemporaryFile("wb", dir=target_dir, delete=False) as tf:
            with open(source_path, "rb") as sf:
                shutil.copyfileobj(sf, tf)
            tf.flush()
            os.fsync(tf.fileno())
            temp_name = tf.name

        self.atomic_publish(temp_name, target_path)
        digest = compute_sha256(target_path)
        return target_path, digest

    def save_manifest(self, run_id: str, manifest_json: str) -> str:
        manifest_path = os.path.join(self.get_run_dir(run_id), "manifest.json")
        self._write_atomic_str(manifest_path, manifest_json)
        return manifest_path

    def save_report(self, run_id: str, report_json: str) -> str:
        report_path = os.path.join(self.get_run_dir(run_id), "report.json")
        self._write_atomic_str(report_path, report_json)
        return report_path

    def verify_file_digest(self, file_path: str, expected_digest: str) -> bool:
        if not os.path.exists(file_path):
            return False
        if not expected_digest.startswith("sha256:"):
            return False
        actual_digest = compute_sha256(file_path)
        return actual_digest == expected_digest

    def verify_run_asset(self, run_id: str, relative_path: str, expected_digest: str) -> bool:
        run_dir = self.get_run_dir(run_id)
        full_path = os.path.join(run_dir, relative_path)
        return self.verify_file_digest(full_path, expected_digest)

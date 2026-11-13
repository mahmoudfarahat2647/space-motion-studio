"""Per-run exclusive lock implementation.

Prevents concurrent writes to the same run and handles stale locks safely
without terminating processes on Windows.
Configures Win32 64-bit handle types to prevent handle truncation.
"""

from datetime import datetime, timezone
import json
import os
import socket
import sys
import time
from contextlib import contextmanager
from space_motion_studio.domain.errors import RunConflictError


class RunLock:
    """Exclusive lock for an isolated run directory."""

    def __init__(self, run_dir: str, run_id: str) -> None:
        self.run_dir = run_dir
        self.run_id = run_id
        self.lock_path = os.path.join(run_dir, ".lock")
        self._is_locked = False

    @contextmanager
    def _guard(self):
        """Serialize lock record changes across threads and processes."""
        guard_path = os.path.join(self.run_dir, ".lock.guard")
        with open(guard_path, "a+b") as guard:
            guard.seek(0, os.SEEK_END)
            if guard.tell() == 0:
                guard.write(b"0")
                guard.flush()
            if sys.platform == "win32":
                import msvcrt
                while True:
                    try:
                        guard.seek(0)
                        msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        time.sleep(0.01)
            else:
                import fcntl
                fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if sys.platform == "win32":
                    guard.seek(0)
                    msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(guard.fileno(), fcntl.LOCK_UN)

    def is_pid_alive(self, pid: int) -> bool:
        """Check if process with given PID is currently alive on Windows/POSIX.

        On Windows, os.kill(pid, 0) calls TerminateProcess(hProcess, 0), which
        terminates the target process! We use Win32 OpenProcess/WaitForSingleObject
        instead to check process existence and liveness without killing it.
        Explicitly sets restype to wintypes.HANDLE to avoid 64-bit handle truncation.
        """
        if pid <= 0:
            return False

        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            # Explicitly declare 64-bit signature types for kernel32 functions
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel32.WaitForSingleObject.restype = wintypes.DWORD
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            kernel32.GetLastError.argtypes = []
            kernel32.GetLastError.restype = wintypes.DWORD

            # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000, SYNCHRONIZE = 0x00100000
            process_flags = 0x1000 | 0x00100000
            wait_timeout = 0x00000102  # WAIT_TIMEOUT (still running)
            error_access_denied = 5

            handle = kernel32.OpenProcess(process_flags, False, pid)
            if not handle:
                error = kernel32.GetLastError()
                # If access is denied, the process exists and is active
                return error == error_access_denied

            try:
                result = kernel32.WaitForSingleObject(handle, 0)
                return result == wait_timeout
            finally:
                kernel32.CloseHandle(handle)
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def acquire(self, max_attempts: int = 5) -> None:
        """Acquire exclusive lock or raise RunConflictError.

        Attempts atomic lock creation first. If already locked, verifies whether
        the holding process is still active. If stale or corrupted, clears it safely
        and retries atomically.
        """
        if self._is_locked:
            return

        os.makedirs(self.run_dir, exist_ok=True)
        my_pid = os.getpid()
        my_host = socket.gethostname()

        payload = {
            "runId": self.run_id,
            "pid": my_pid,
            "host": my_host,
            "acquiredAt": datetime.now(timezone.utc).isoformat(),
        }
        payload_bytes = json.dumps(payload, indent=2).encode("utf-8")

        with self._guard():
            self._acquire_guarded(payload_bytes, my_host)

    def _acquire_guarded(self, payload_bytes: bytes, my_host: str) -> None:
        for attempt in range(2):
            # 1. Attempt atomic creation: fails if file already exists
            try:
                flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
                fd = os.open(self.lock_path, flags)
                try:
                    os.write(fd, payload_bytes)
                finally:
                    os.close(fd)
                self._is_locked = True
                return
            except FileExistsError:
                pass

            # 2. Lock file exists: inspect owner, accounting for concurrent writes
            lock_data = None
            for _ in range(5):
                try:
                    with open(self.lock_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if content.strip():
                        lock_data = json.loads(content)
                        break
                except (OSError, json.JSONDecodeError):
                    pass
                time.sleep(0.05)

            if lock_data is None:
                # Corrupted or unreadable lock file after retries; clear and retry
                try:
                    os.remove(self.lock_path)
                except OSError:
                    pass
                continue

            locked_pid = lock_data.get("pid")
            locked_host = lock_data.get("host")

            # Check if holding process is alive on the same host
            if locked_host != my_host or not isinstance(locked_pid, int) or self.is_pid_alive(locked_pid):
                raise RunConflictError(
                    f"Run '{self.run_id}' is currently locked by active process PID {locked_pid} on {locked_host}"
                )

            # Stale lock: clean up safely only if file still matches this stale lock
            try:
                with open(self.lock_path, "r", encoding="utf-8") as f:
                    current = f.read()
                if json.loads(current).get("pid") == locked_pid:
                    os.remove(self.lock_path)
            except OSError:
                pass
            except json.JSONDecodeError:
                try:
                    os.remove(self.lock_path)
                except OSError:
                    pass

        # If still unable to acquire after max_attempts
        raise RunConflictError(
            f"Concurrent conflict: unable to acquire exclusive lock for run '{self.run_id}'"
        )

    def release(self) -> None:
        """Release lock if owned by this instance."""
        if not self._is_locked:
            return

        with self._guard():
            self._release_guarded()

    def _release_guarded(self) -> None:
        if not os.path.exists(self.lock_path):
            self._is_locked = False
            return

        try:
            with open(self.lock_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("pid") == os.getpid() and data.get("host") == socket.gethostname():
                os.remove(self.lock_path)
        except Exception:
            pass
        finally:
            self._is_locked = False

    def __enter__(self) -> "RunLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

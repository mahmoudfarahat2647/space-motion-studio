"""Tests for run isolation, locking, atomic writes, and digest validation."""

from concurrent.futures import ThreadPoolExecutor
import os
import socket
import tempfile
import pytest
from space_motion_studio.adapters.storage.fs_storage import FileSystemRunStorage, compute_sha256
from space_motion_studio.adapters.storage.run_lock import RunLock
from space_motion_studio.domain.errors import RunConflictError


def test_pid_liveness_check_safe_on_windows_and_posix():
    """Verify that PID liveness check detects active PID without terminating on Windows."""
    lock = RunLock("dummy", "dummy")
    current_pid = os.getpid()

    # Current process must be alive
    assert lock.is_pid_alive(current_pid) is True
    # Nonexistent PID must be reported as dead
    assert lock.is_pid_alive(9999999) is False
    # Non-positive PIDs must return False
    assert lock.is_pid_alive(0) is False
    assert lock.is_pid_alive(-1) is False


def test_run_lock_prevents_concurrent_writes():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_id = "test-run-concurrent"
        lock1 = RunLock(tmpdir, run_id)
        lock2 = RunLock(tmpdir, run_id)

        # Acquire lock 1
        lock1.acquire()
        assert os.path.exists(lock1.lock_path)

        # Lock 2 must raise RunConflictError
        with pytest.raises(RunConflictError):
            lock2.acquire()

        # Release lock 1
        lock1.release()
        assert not os.path.exists(lock1.lock_path)

        # Lock 2 can now acquire
        lock2.acquire()
        assert os.path.exists(lock2.lock_path)
        lock2.release()


def test_run_lock_context_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_id = "test-run-cm"
        lock = RunLock(tmpdir, run_id)

        with lock:
            assert os.path.exists(lock.lock_path)

        assert not os.path.exists(lock.lock_path)


def test_run_lock_concurrent_race_threads():
    """Test race condition resilience: exactly one thread must acquire the lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_id = "test-race-threads"
        successes = []
        conflicts = []

        def worker(thread_id: int):
            lock = RunLock(tmpdir, run_id)
            try:
                lock.acquire()
                successes.append(thread_id)
            except RunConflictError:
                conflicts.append(thread_id)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(worker, i) for i in range(8)]
            for f in futures:
                f.result()

        assert len(successes) == 1
        assert len(conflicts) == 7


def test_stale_lock_recovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_id = "test-run-stale"
        lock_path = os.path.join(tmpdir, ".lock")
        # Write lock with non-existent PID (e.g. 9999999) and current hostname
        with open(lock_path, "w", encoding="utf-8") as f:
            f.write('{"runId": "test-run-stale", "pid": 9999999, "host": "' + socket.gethostname() + '"}')

        lock = RunLock(tmpdir, run_id)
        # Should clear stale lock and acquire successfully
        lock.acquire()
        assert os.path.exists(lock.lock_path)
        lock.release()


def test_corrupt_lock_file_recovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_id = "test-run-corrupt"
        lock_path = os.path.join(tmpdir, ".lock")
        # Write corrupted garbage into lock file
        with open(lock_path, "w", encoding="utf-8") as f:
            f.write("{corrupt json garbage...")

        lock = RunLock(tmpdir, run_id)
        lock.acquire()
        assert os.path.exists(lock.lock_path)
        lock.release()


def test_atomic_file_publishing():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileSystemRunStorage(base_runs_dir=tmpdir)
        run_id = "test-atomic"
        storage.create_run(run_id)

        target_file = os.path.join(storage.get_run_dir(run_id), "output.txt")
        temp_file = os.path.join(storage.get_run_dir(run_id), "output.tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("Hello Atomic World")

        storage.atomic_publish(temp_file, target_file)
        assert os.path.exists(target_file)
        assert not os.path.exists(temp_file)

        with open(target_file, "r", encoding="utf-8") as f:
            assert f.read() == "Hello Atomic World"


def test_sha256_digest_verification():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileSystemRunStorage(base_runs_dir=tmpdir)
        test_file = os.path.join(tmpdir, "data.bin")
        with open(test_file, "wb") as f:
            f.write(b"Reliable binary digest test")

        digest = compute_sha256(test_file)
        assert digest.startswith("sha256:")
        assert storage.verify_file_digest(test_file, digest) is True
        assert storage.verify_file_digest(test_file, "sha256:wrongdigest") is False
        assert storage.verify_file_digest(test_file, "invalid") is False


@pytest.mark.parametrize("run_id", ["..", "../other", "..\\other", "C:\\other", ""])
def test_run_id_cannot_escape_storage(tmp_path, run_id):
    with pytest.raises(ValueError):
        FileSystemRunStorage(str(tmp_path)).get_run_dir(run_id)


def test_foreign_host_lock_is_not_stolen(tmp_path):
    lock = RunLock(str(tmp_path), "run")
    with open(lock.lock_path, "w", encoding="utf-8") as f:
        import json
        json.dump({"pid": 9999999, "host": "another-host"}, f)
    with pytest.raises(RunConflictError):
        lock.acquire()

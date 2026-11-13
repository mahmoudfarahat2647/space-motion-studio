"""Tests for preflight system diagnostics."""

import io
import sys
from space_motion_studio.adapters.preflight.diagnostics import SystemPreflightAdapter
from space_motion_studio.entrypoints.cli import run_preflight_command


def test_preflight_diagnostics_pass():
    adapter = SystemPreflightAdapter()
    report = adapter.run_diagnostics()

    assert report.all_passed is True, f"Preflight checks failed: {[c for c in report.checks if not c.passed]}"
    check_names = {c.name for c in report.checks}
    assert "Python" in check_names
    assert "Node.js" in check_names
    assert "pnpm" in check_names
    assert "FFmpeg" in check_names
    assert "FFprobe" in check_names
    assert "Browser" in check_names


def test_preflight_cli_cp1256_encoding_regression(monkeypatch):
    """Regression test: on Windows with cp1256 console, preflight output must not raise UnicodeEncodeError."""
    byte_buffer = io.BytesIO()
    # Create a stream with strict cp1256 encoding to simulate Arabic Windows terminal
    cp1256_stream = io.TextIOWrapper(byte_buffer, encoding="cp1256", errors="strict")
    monkeypatch.setattr(sys, "stdout", cp1256_stream)

    exit_code = run_preflight_command()
    cp1256_stream.flush()

    assert exit_code == 0
    output_text = byte_buffer.getvalue().decode("cp1256")
    assert "Preflight Diagnostics" in output_text
    assert "[OK]" in output_text

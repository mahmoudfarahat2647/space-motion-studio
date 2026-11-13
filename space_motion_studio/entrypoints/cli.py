"""Command Line Interface for Space Motion Studio.

Provides public production commands and preflight diagnostics.
Handles Windows console codepages (such as cp1256) safely without UnicodeEncodeError.
"""

import argparse
import sys
from space_motion_studio.adapters.preflight.diagnostics import SystemPreflightAdapter
from space_motion_studio.domain.errors import DomainError
from space_motion_studio.entrypoints.composition_root import build_produce_demo_use_case


def configure_console_streams() -> None:
    """Ensure standard streams handle UTF-8 safely with fallback on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def run_preflight_command() -> int:
    """Run preflight diagnostics and print human-readable status."""
    adapter = SystemPreflightAdapter()
    report = adapter.run_diagnostics()

    print("==================================================")
    print("Space Motion Studio -- Preflight Diagnostics")
    print("==================================================")
    for check in report.checks:
        status_symbol = "[OK]" if check.passed else "[FAIL]"
        print(f"{status_symbol:6} {check.name:10} : {check.message}")
    print("--------------------------------------------------")

    if report.all_passed:
        print("Preflight check PASSED: All required dependencies are satisfied.")
        return 0
    else:
        print("Preflight check FAILED: Please install or configure missing dependencies.")
        return 1


def run_produce_command(args: argparse.Namespace) -> int:
    """Execute video production."""
    if not getattr(args, "demo", False):
        print("Error: For this release milestone, please run with '--demo' to render the offline demo.", file=sys.stderr)
        return 1

    print("Starting Space Motion Studio demo production...")
    try:
        runs_dir = getattr(args, "runs_dir", "runs") or "runs"
        use_case = build_produce_demo_use_case(runs_dir=runs_dir)
        report = use_case.execute(run_id=args.run_id)

        print("==================================================")
        print("Production COMPLETED successfully!")
        print("==================================================")
        print(f"Run ID      : {report.run_id}")
        print(f"Status      : {report.status}")
        print(f"Input Digest: {report.input_digest}")
        print("Completed Stages:")
        for stage in report.stages:
            print(f"  - {stage.name}: {stage.status} (finished at {stage.completed_at})")
        print("Output Exports:")
        for out in report.outputs:
            print(f"  - [{out.orientation.upper()}] {out.path}")
            print(f"    Dimensions  : {out.width}x{out.height} @ {out.fps:.1f} fps")
            print(f"    Total Frames: {out.total_frames} ({out.duration_seconds:.2f}s)")
            print(f"    Codecs      : Video={out.video_codec} ({out.pixel_format}), Audio={out.audio_codec} ({out.audio_sample_rate} Hz)")
            print(f"    File Size   : {out.file_size_bytes} bytes")
        print("Asset Credits:")
        for credit in report.asset_credits:
            print(f"  - {credit}")
        return 0

    except DomainError as err:
        print(f"Production error: {err}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="space-motion-studio",
        description="Automated Arabic Motion Graphics Video Pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # produce
    produce_parser = subparsers.add_parser("produce", help="Produce video from topic, storyboard, or demo")
    produce_parser.add_argument("--demo", action="store_true", help="Render the bundled offline single-scene demo")
    produce_parser.add_argument("--run-id", type=str, default=None, help="Optional explicit run ID")
    produce_parser.add_argument("--runs-dir", type=str, default="runs", help="Base directory for run artifacts")

    # demo (shorthand for produce --demo)
    demo_parser = subparsers.add_parser("demo", help="Shorthand to render the bundled offline demo")
    demo_parser.add_argument("--run-id", type=str, default=None, help="Optional explicit run ID")
    demo_parser.add_argument("--runs-dir", type=str, default="runs", help="Base directory for run artifacts")

    # preflight
    subparsers.add_parser("preflight", help="Run system dependency diagnostics")

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_console_streams()
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "preflight":
        return run_preflight_command()
    elif args.command == "demo":
        args.demo = True
        return run_produce_command(args)
    elif args.command == "produce":
        return run_produce_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

# Space Motion Studio

Automated Arabic Motion Graphics Video Pipeline for science and space explainers.

## Prerequisites

- **Windows 10/11** (or compatible OS)
- **Python >= 3.10**
- **Node.js >= 18**
- **pnpm >= 9** (all Node toolchains strictly use pnpm)
- **FFmpeg & FFprobe** available on system PATH

## Documented Setup

Follow these steps on a fresh installation:

1. **Install Node.js dependencies**:
   ```pwsh
   pnpm install
   ```

2. **Ensure provisioned Remotion browser shell**:
   ```pwsh
   pnpm exec remotion browser ensure
   ```

3. **Install Python package and dependencies**:
   ```pwsh
   pip install -e .
   ```
   Or install requirements directly:
   ```pwsh
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Verify toolchain with Preflight Diagnostics**:
   ```pwsh
   space-motion-studio preflight
   # Or using module syntax:
   python -m space_motion_studio preflight
   ```

## Offline Demo Production

The repository includes a bundled single-scene Egyptian Arabic Black Hole explainer with local narration, vector illustration, and the Cairo font. It renders completely offline without any API credentials or network access:

```pwsh
space-motion-studio demo
# Or:
python -m space_motion_studio demo
```

To render to a custom runs directory or specify a run ID:
```pwsh
space-motion-studio demo --run-id my-first-demo --runs-dir runs
```

Rendered outputs:
- Video export: `runs/<run_id>/exports/landscape.mp4` (1920x1080 @ 30 fps, H.264/yuv420p video, AAC 48 kHz audio)
- Storyboard snapshot: `runs/<run_id>/storyboard.json`
- Prepared manifest: `runs/<run_id>/manifest.json`
- Run report: `runs/<run_id>/report.json`

## Development and Verification

- **TypeScript Typecheck**:
  ```pwsh
  pnpm exec tsc --noEmit
  ```

- **Run Pytest Suite**:
  ```pwsh
  python -m pytest -q
  ```

## Architecture

This project strictly follows Clean Architecture:
- `space_motion_studio/domain`: Core domain models and business errors. Independent of frameworks and outer layers.
- `space_motion_studio/application`: Pure use cases (timeline compilation, run preparation, demo coordination) and ports. Free of filesystem (`os.path`), network, and library leakage.
- `space_motion_studio/adapters`: External integrations (FFprobe inspector, Remotion CLI renderer, filesystem storage with atomic publishing, Pydantic schemas, preflight diagnostics).
- `space_motion_studio/entrypoints`: CLI argument parsing and composition root wiring concrete adapters to use cases via Dependency Inversion.

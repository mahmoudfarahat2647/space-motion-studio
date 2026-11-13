"""Tests for the pure timeline compiler use case."""

import pytest
from space_motion_studio.application.use_cases.compile_timeline import CompileTimelineUseCase
from space_motion_studio.domain.errors import ValidationError


def test_compile_single_scene():
    compiler = CompileTimelineUseCase()
    # 6.72s at 30 fps
    # audio frames = ceil(6.72 * 30) = ceil(201.6) = 202
    # trailing pause = ceil(0.4 * 30) = 12
    # scene frames = 202 + 12 = 214
    schedule = compiler.execute([6.72], fps=30, trailing_pause_seconds=0.4)
    assert schedule.fps == 30
    assert schedule.total_frame_count == 214
    assert len(schedule.scenes) == 1

    scene0 = schedule.scenes[0]
    assert scene0.start_frame == 0
    assert scene0.audio_frame_count == 202
    assert scene0.trailing_pause_frames == 12
    assert scene0.scene_frame_count == 214


def test_compile_multiple_scenes_cumulative_starts():
    compiler = CompileTimelineUseCase()
    durations = [2.0, 3.5, 1.1]
    # At 30 fps, trailing pause 0.4s (12 frames):
    # Scene 0: ceil(2.0*30) = 60 + 12 = 72 frames -> start 0
    # Scene 1: ceil(3.5*30) = 105 + 12 = 117 frames -> start 72
    # Scene 2: ceil(1.1*30) = 33 + 12 = 45 frames -> start 72 + 117 = 189
    # Total = 72 + 117 + 45 = 234 frames
    schedule = compiler.execute(durations, fps=30, trailing_pause_seconds=0.4)
    assert schedule.total_frame_count == 234

    assert schedule.scenes[0].start_frame == 0
    assert schedule.scenes[0].scene_frame_count == 72

    assert schedule.scenes[1].start_frame == 72
    assert schedule.scenes[1].scene_frame_count == 117

    assert schedule.scenes[2].start_frame == 189
    assert schedule.scenes[2].scene_frame_count == 45


def test_compile_invalid_inputs():
    compiler = CompileTimelineUseCase()
    with pytest.raises(ValidationError):
        compiler.execute([], fps=30)

    with pytest.raises(ValidationError):
        compiler.execute([2.0], fps=0)

    with pytest.raises(ValidationError):
        compiler.execute([-1.0], fps=30)

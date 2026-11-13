"""Timeline compilation use case.

Following Clean Architecture and SPEC.md Decision 11:
One single timeline authority in Python converts measured audio durations into
exact audio frames and trailing pause frames, computes cumulative scene starts,
and determines total frame count.
"""

import math
from dataclasses import dataclass
from space_motion_studio.domain.errors import ValidationError


@dataclass(frozen=True)
class SceneSchedule:
    start_frame: int
    audio_frame_count: int
    trailing_pause_frames: int
    scene_frame_count: int


@dataclass(frozen=True)
class TimelineSchedule:
    fps: int
    total_frame_count: int
    scenes: tuple[SceneSchedule, ...]


class CompileTimelineUseCase:
    """Pure application timeline compiler."""

    def execute(
        self,
        audio_durations: list[float] | tuple[float, ...],
        fps: int = 30,
        trailing_pause_seconds: float = 0.4,
    ) -> TimelineSchedule:
        if fps <= 0:
            raise ValidationError(f"FPS must be positive, got {fps}", "fps")
        if not audio_durations:
            raise ValidationError("Audio durations list cannot be empty", "scenes")
        if trailing_pause_seconds < 0:
            raise ValidationError("Trailing pause must be non-negative", "trailing_pause_seconds")

        trailing_pause_frames = math.ceil(trailing_pause_seconds * fps)
        scenes: list[SceneSchedule] = []
        current_frame = 0

        for idx, duration in enumerate(audio_durations):
            if duration < 0 or not math.isfinite(duration):
                raise ValidationError(
                    f"Invalid audio duration at scene {idx}: {duration}",
                    f"scenes[{idx}].measuredAudioDuration",
                )
            audio_frames = math.ceil(duration * fps)
            scene_frames = audio_frames + trailing_pause_frames

            scenes.append(
                SceneSchedule(
                    start_frame=current_frame,
                    audio_frame_count=audio_frames,
                    trailing_pause_frames=trailing_pause_frames,
                    scene_frame_count=scene_frames,
                )
            )
            current_frame += scene_frames

        return TimelineSchedule(
            fps=fps,
            total_frame_count=current_frame,
            scenes=tuple(scenes),
        )

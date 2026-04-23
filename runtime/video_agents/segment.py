"""Beat-aware segment packing for Slate.

Example:
    >>> scenes = [
    ...     SceneSpec(scene_id='scene-1', order=1, title='A', location='bridge', time_of_day='day', summary='a', target_shot_count=1),
    ... ]
    >>> beats = [
    ...     StoryBeat(beat_id='beat-1', scene_id='scene-1', order=1, label='L1', purpose='p', summary='s', duration_seconds=6),
    ...     StoryBeat(beat_id='beat-2', scene_id='scene-1', order=2, label='L2', purpose='p', summary='s', duration_seconds=5),
    ... ]
    >>> shots = []
    >>> len(pack_segments(scenes, beats, shots, 15))
    1
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import SceneSpec, Segment, Shot, StoryBeat


class SingleBeatTooLongError(Exception):
    """Raised when one beat alone exceeds the segment budget."""

    def __init__(self, beat_id: str, duration: float, max_seconds: float):
        super().__init__(f"Beat {beat_id!r} duration {duration} exceeds max segment {max_seconds}.")
        self.beat_id = beat_id
        self.duration = duration
        self.max_seconds = max_seconds


@dataclass
class _WorkingSegment:
    scene_id: str
    beat_ids: list[str]
    shot_ids: list[str]
    duration_seconds: float


def _finalize(segment: _WorkingSegment, index: int) -> Segment:
    return Segment(
        segment_id=f"segment-{index:02d}",
        beat_ids=list(segment.beat_ids),
        shot_ids=list(segment.shot_ids),
        duration_seconds=segment.duration_seconds,
    )


def pack_segments(
    scenes: list[SceneSpec],
    beats: list[StoryBeat],
    shots: list[Shot],
    max_segment_seconds: float,
) -> list[Segment]:
    """Pack beats into segments without crossing scenes."""

    if max_segment_seconds <= 0:
        raise ValueError("max_segment_seconds must be positive.")

    shots_by_beat: dict[str, list[str]] = {}
    for shot in shots:
        shots_by_beat.setdefault(shot.beat_id, []).append(shot.shot_id)

    scene_order = {scene.scene_id: scene.order for scene in scenes}
    ordered_beats = sorted(
        beats,
        key=lambda beat: (scene_order.get(beat.scene_id, 10**9), beat.order),
    )

    working_segments: list[_WorkingSegment] = []
    current: _WorkingSegment | None = None

    for beat in ordered_beats:
        if beat.duration_seconds > max_segment_seconds:
            raise SingleBeatTooLongError(beat.beat_id, beat.duration_seconds, max_segment_seconds)

        if current is None or current.scene_id != beat.scene_id:
            if current is not None:
                working_segments.append(current)
            current = _WorkingSegment(
                scene_id=beat.scene_id,
                beat_ids=[beat.beat_id],
                shot_ids=list(shots_by_beat.get(beat.beat_id, [])),
                duration_seconds=beat.duration_seconds,
            )
            continue

        if current.duration_seconds + beat.duration_seconds > max_segment_seconds:
            working_segments.append(current)
            current = _WorkingSegment(
                scene_id=beat.scene_id,
                beat_ids=[beat.beat_id],
                shot_ids=list(shots_by_beat.get(beat.beat_id, [])),
                duration_seconds=beat.duration_seconds,
            )
            continue

        current.beat_ids.append(beat.beat_id)
        current.shot_ids.extend(shots_by_beat.get(beat.beat_id, []))
        current.duration_seconds += beat.duration_seconds

    if current is not None:
        working_segments.append(current)

    if len(working_segments) >= 2:
        last = working_segments[-1]
        prev = working_segments[-2]
        if (
            last.scene_id == prev.scene_id
            and last.duration_seconds < max_segment_seconds * 0.3
            and len(prev.beat_ids) > 1
        ):
            borrowed_beat_id = prev.beat_ids[-1]
            borrowed_shots = shots_by_beat.get(borrowed_beat_id, [])
            borrowed_beat = next(beat for beat in ordered_beats if beat.beat_id == borrowed_beat_id)
            if last.duration_seconds + borrowed_beat.duration_seconds <= max_segment_seconds:
                prev.beat_ids.pop()
                for shot_id in reversed(borrowed_shots):
                    if shot_id in prev.shot_ids:
                        prev.shot_ids.remove(shot_id)
                prev.duration_seconds -= borrowed_beat.duration_seconds
                last.beat_ids.insert(0, borrowed_beat_id)
                last.shot_ids = list(borrowed_shots) + last.shot_ids
                last.duration_seconds += borrowed_beat.duration_seconds

    return [_finalize(segment, index + 1) for index, segment in enumerate(working_segments)]

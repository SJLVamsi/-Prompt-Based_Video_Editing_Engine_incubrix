"""Keep: keep only listed ranges, drop the rest. Empty keeps = error."""
from __future__ import annotations

from ..errors import TimelineValidationError
from ..schema import Clip, Timeline, evolve_timeline
from .ranges import normalize_ranges


def op_keep(tl: Timeline, ranges: list[tuple[int, int]]) -> Timeline:
    if not ranges:
        raise TimelineValidationError("EMPTY_TIMELINE", "keep with empty ranges would drop everything")
    duration = max((c.end_frame for c in tl.clips), default=0)
    keeps = normalize_ranges(ranges, duration)
    # intersect keeps with existing clips
    new_spans: list[tuple[int, int]] = []
    for cs, ce in [(c.start_frame, c.end_frame) for c in tl.clips]:
        for ks, ke in keeps:
            s, e = max(cs, ks), min(ce, ke)
            if s < e:
                new_spans.append((s, e))
    if not new_spans:
        raise TimelineValidationError("EMPTY_TIMELINE", "keep selects nothing")
    # no-op detection: identical spans
    old_spans = [(c.start_frame, c.end_frame) for c in tl.clips]
    if new_spans == old_spans:
        return tl
    new_clips = [
        Clip(
            id=f"{tl.clips[0].id}#k{i}" if len(new_spans) > 1 else tl.clips[0].id,
            source_id=tl.clips[0].source_id,
            start_frame=s,
            end_frame=e,
            speed_num=tl.clips[0].speed_num,
            speed_den=tl.clips[0].speed_den,
        )
        for i, (s, e) in enumerate(new_spans)
    ]
    return evolve_timeline(tl, clips=tuple(new_clips))

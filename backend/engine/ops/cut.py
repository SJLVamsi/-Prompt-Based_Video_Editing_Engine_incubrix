"""Cut: remove ranges from timeline (split clips). Empty = no-op."""
from __future__ import annotations

from ..errors import TimelineValidationError
from ..schema import Clip, Timeline, evolve_timeline
from .ranges import normalize_ranges, subtract_range


def _timeline_span(tl: Timeline) -> int:
    if not tl.clips:
        return 0
    return max(c.end_frame for c in tl.clips)


def op_cut(tl: Timeline, ranges: list[tuple[int, int]]) -> Timeline:
    if not ranges:
        return tl  # no-op: same object/hash
    duration = _timeline_span(tl)
    cuts = normalize_ranges(ranges, duration)
    # apply cuts to each clip span
    spans: list[tuple[int, int]] = [(c.start_frame, c.end_frame) for c in tl.clips]
    for cut in cuts:
        spans = subtract_range(spans, cut)
    if not spans:
        raise TimelineValidationError("EMPTY_TIMELINE", "cut removes everything; need >=1 frame")
    # rebuild clips preserving source/speed/anchors where span survives; split as needed
    new_clips: list[Clip] = []
    for idx, (s, e) in enumerate(spans):
        # find origin clip containing s (original clips may have been split)
        origin = next((c for c in tl.clips if c.start_frame <= s < c.end_frame), tl.clips[0])
        new_clips.append(
            Clip(
                id=f"{origin.id}#c{idx}" if len(spans) > 1 else origin.id,
                source_id=origin.source_id,
                start_frame=s,
                end_frame=e,
                speed_num=origin.speed_num,
                speed_den=origin.speed_den,
                anchor_start_word_id=origin.anchor_start_word_id,
                anchor_end_word_id=origin.anchor_end_word_id,
            )
        )
    # filter captions fully inside removed region? keep captions, but drop those with zero overlap
    kept_set = spans
    new_captions = []
    for cap in tl.captions:
        overlaps = any(not (cap.end_frame <= s or cap.start_frame >= e) for s, e in kept_set)
        if overlaps:
            new_captions.append(cap)
    return evolve_timeline(tl, clips=tuple(new_clips), captions=tuple(new_captions))

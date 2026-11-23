"""Captions: add/remove. Overlap allowed (stack); identical duplicate rejected."""
from __future__ import annotations

import itertools

from ..errors import TimelineValidationError
from ..schema import Caption, Timeline, evolve_timeline

_counter = itertools.count(1)


def op_caption_add(
    tl: Timeline,
    text: str,
    start_frame: int,
    end_frame: int,
    style: str = "subtitle",
    anchor_start_word_id: str | None = None,
    anchor_end_word_id: str | None = None,
    caption_id: str | None = None,
) -> Timeline:
    if not text.strip():
        raise TimelineValidationError("EMPTY_CAPTION", "caption text must be non-empty")
    if end_frame <= start_frame:
        raise TimelineValidationError("ZERO_LENGTH", "caption end must be > start")
    if len(text) > 240:
        raise TimelineValidationError("BAD_CAPTION", "caption text too long (>240 chars)")
    duration = max((c.end_frame for c in tl.clips), default=0)
    if start_frame < 0 or end_frame > duration:
        raise TimelineValidationError("OUT_OF_BOUNDS", "caption outside timeline")
    for cap in tl.captions:
        if cap.text == text and cap.start_frame == start_frame and cap.end_frame == end_frame:
            raise TimelineValidationError("DUPLICATE_CAPTION", "identical caption already exists")
    cid = caption_id or f"cap{next(_counter):04d}"
    new_cap = Caption(cid, text, start_frame, end_frame, style, anchor_start_word_id, anchor_end_word_id)
    return evolve_timeline(tl, captions=tuple(sorted((*tl.captions, new_cap), key=lambda c: (c.start_frame, c.id))))


def op_caption_remove(tl: Timeline, caption_id: str) -> Timeline:
    remaining = tuple(c for c in tl.captions if c.id != caption_id)
    if len(remaining) == len(tl.captions):
        raise TimelineValidationError("NOT_FOUND", f"caption {caption_id} not found")
    return evolve_timeline(tl, captions=remaining)

"""Range normalize helpers shared by ops."""
from __future__ import annotations

from ..errors import TimelineValidationError


def normalize_ranges(ranges: list[tuple[int, int]], duration: int) -> list[tuple[int, int]]:
    """Sort, validate, coalesce overlapping/adjacent ranges. Rejects zero-length/oob."""
    if not ranges:
        return []
    cleaned: list[tuple[int, int]] = []
    for s, e in ranges:
        if e <= s:
            raise TimelineValidationError("ZERO_LENGTH", f"range end must be > start: {(s, e)}")
        if s < 0 or e < 0:
            raise TimelineValidationError("OUT_OF_BOUNDS", f"range negative: {(s, e)}")
        if s >= duration or e > duration:
            raise TimelineValidationError("OUT_OF_BOUNDS", f"range {(s, e)} outside duration {duration}")
        cleaned.append((s, e))
    cleaned.sort()
    merged: list[list[int]] = [[cleaned[0][0], cleaned[0][1]]]
    for s, e in cleaned[1:]:
        if s <= merged[-1][1]:  # overlap or adjacent -> merge
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def complement_ranges(kept: list[tuple[int, int]], duration: int) -> list[tuple[int, int]]:
    """Invert kept ranges within [0, duration)."""
    out: list[tuple[int, int]] = []
    cursor = 0
    for s, e in kept:
        if cursor < s:
            out.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration:
        out.append((cursor, duration))
    return out


def subtract_range(clips: list[tuple[int, int]], cut: tuple[int, int]) -> list[tuple[int, int]]:
    """Subtract single cut (cs,ce) from list of [s,e) spans."""
    cs, ce = cut
    out: list[tuple[int, int]] = []
    for s, e in clips:
        if ce <= s or cs >= e:
            out.append((s, e))
        else:
            if cs > s:
                out.append((s, cs))
            if ce < e:
                out.append((ce, e))
    return out

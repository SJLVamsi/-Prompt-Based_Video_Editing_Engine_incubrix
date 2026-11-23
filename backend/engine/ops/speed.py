"""Speed: set speed on range. Captions inside scale. Overlapping speeds rejected."""
from __future__ import annotations

from ..errors import TimelineValidationError
from ..schema import Caption, Clip, Timeline, evolve_timeline


def op_speed(tl: Timeline, start_frame: int, end_frame: int, num: int, den: int) -> Timeline:
    if den == 0 or num <= 0 or den <= 0:
        raise TimelineValidationError("BAD_SPEED", f"invalid speed {num}/{den}")
    if num / den < 0.25 or num / den > 4.0:
        raise TimelineValidationError("BAD_SPEED", f"speed {num}/{den} outside 0.25-4x")
    if end_frame <= start_frame:
        raise TimelineValidationError("ZERO_LENGTH", "speed range end must be > start")
    if end_frame - start_frame < 5:
        raise TimelineValidationError("BAD_SPEED", "speed range too short (<5 frames)")
    duration = max((c.end_frame for c in tl.clips), default=0)
    if start_frame < 0 or end_frame > duration:
        raise TimelineValidationError("OUT_OF_BOUNDS", "speed range outside timeline")
    # reject overlapping existing speeds: any clip already non-1x overlapping range
    for c in tl.clips:
        if (c.speed_num, c.speed_den) != (1, 1) and not (end_frame <= c.start_frame or start_frame >= c.end_frame):
            raise TimelineValidationError("BAD_SPEED", f"overlapping speed on clip {c.id}")
    new_clips: list[Clip] = []
    for c in tl.clips:
        if end_frame <= c.start_frame or start_frame >= c.end_frame:
            new_clips.append(c)
            continue
        # split into left/mid/right
        if start_frame > c.start_frame:
            new_clips.append(Clip(f"{c.id}#pre", c.source_id, c.start_frame, start_frame,
                                  c.speed_num, c.speed_den, c.anchor_start_word_id, c.anchor_end_word_id))
        new_clips.append(Clip(f"{c.id}#sp", c.source_id, max(c.start_frame, start_frame),
                              min(c.end_frame, end_frame), num, den,
                              c.anchor_start_word_id, c.anchor_end_word_id))
        if end_frame < c.end_frame:
            new_clips.append(Clip(f"{c.id}#post", c.source_id, end_frame, c.end_frame,
                                  c.speed_num, c.speed_den, c.anchor_start_word_id, c.anchor_end_word_id))
    # rescale captions intersecting the sped range
    new_caps: list[Caption] = []
    for cap in tl.captions:
        if cap.end_frame <= start_frame or cap.start_frame >= end_frame:
            new_caps.append(cap)
            continue
        # scale positions relative to range start: new = rs + (old-rs)*den/num
        def scale(f: int) -> int:
            return start_frame + round((f - start_frame) * den / num)
        ns = scale(max(cap.start_frame, start_frame))
        ne = scale(min(cap.end_frame, end_frame))
        # keep outside parts? simplify: scale whole caption if fully inside, else keep original + warn by clamping
        if cap.start_frame >= start_frame and cap.end_frame <= end_frame and ne > ns:
            new_caps.append(Caption(cap.id, cap.text, ns, ne, cap.style,
                                    cap.anchor_start_word_id, cap.anchor_end_word_id))
        else:
            new_caps.append(cap)
    return evolve_timeline(tl, clips=tuple(new_clips), captions=tuple(new_caps))

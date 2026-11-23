"""Rational timebase helpers. Integer math inside, floats only at emission."""
from __future__ import annotations

from fractions import Fraction


def t_to_frame(t: Fraction | float, fps_num: int, fps_den: int = 1) -> int:
    """frame = round(t * fps_num/fps_den). Accepts Fraction (preferred) or float."""
    fps = Fraction(fps_num, fps_den)
    if isinstance(t, float):
        t = Fraction(t).limit_denominator(1_000_000)
    return int(round(t * fps))


def frame_to_t(frame: int, fps_num: int, fps_den: int = 1) -> Fraction:
    """t = frame * fps_den/fps_num as exact Fraction."""
    if frame < 0:
        raise ValueError("frame must be >= 0")
    return Fraction(frame, 1) * Fraction(fps_den, fps_num)


def frame_to_pts(frame: int, fps_num: int, fps_den: int, tb_num: int, tb_den: int) -> int:
    """Convert frame -> integer pts in given timebase."""
    t = frame_to_t(frame, fps_num, fps_den)
    tb = Fraction(tb_num, tb_den)
    return int(round(t / tb))


def frame_to_sec_str(frame: int, fps_num: int, fps_den: int, ndigits: int = 6) -> str:
    """Decimal seconds string for FFmpeg atrim (emission layer only)."""
    t = frame_to_t(frame, fps_num, fps_den)
    return f"{float(t):.{ndigits}f}"


def parse_r_frame_rate(s: str) -> tuple[int, int]:
    """Parse '30000/1001' or '30' or '30/1' -> (num, den)."""
    s = s.strip()
    if "/" in s:
        num_s, den_s = s.split("/", 1)
        num, den = int(num_s), int(den_s)
    else:
        num, den = int(float(s)), 1
        # keep common case exact: "29.97" -> 30000/1001 handled by caller if needed
    if den == 0:
        raise ValueError("frame rate denominator must be non-zero")
    return num, den

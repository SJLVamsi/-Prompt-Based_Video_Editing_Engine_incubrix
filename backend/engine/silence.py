"""Silence handling: word-gap shortener (primary) + silencedetect preview helper."""
from __future__ import annotations

from .schema import Word


def word_gap_cuts(
    words: tuple[Word, ...] | list[Word],
    fps_num: int,
    fps_den: int,
    min_gap_sec: float = 0.5,
    target_gap_sec: float = 0.3,
) -> list[tuple[int, int]]:
    """For each inter-word gap >= min_gap, cut the middle so remainder == target.

    Keeps natural padding at both edges. Returns frame ranges to cut.
    """
    from fractions import Fraction
    min_gap_f = round(min_gap_sec * fps_num / fps_den)
    target_f = round(target_gap_sec * fps_num / fps_den)
    cuts: list[tuple[int, int]] = []
    words = list(words)
    for a, b in zip(words, words[1:]):
        gap_s, gap_e = a.end_frame, b.start_frame
        L = gap_e - gap_s
        if L >= min_gap_f and L > target_f:
            excess = L - target_f
            cs = gap_s + (L - excess) // 2 - excess // 2 + excess // 2  # centered
            # simpler centered: middle `excess` frames
            cs = gap_s + (L - excess) // 2
            # Actually keep target centered: cut middle excess
            cs = gap_s + (L - excess) // 2 + (0 if excess % 2 == 0 else 0)
            # recompute cleanly:
            cs = gap_s + (L - excess) // 2
            ce = cs + excess
            # NOTE: (L-excess)==target so cs = gap_s + target//2
            cuts.append((cs, ce))
    return cuts


def silencedetect_preview_args(noise_db: float = -50.0, min_dur: float = 0.5) -> list[str]:
    """Return ffmpeg filter args for preview (no exec)."""
    return ["-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"]

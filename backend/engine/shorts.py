"""Shorts planner: knapsack fit + hook score + 9:16 crop params. Pure."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Beat:
    id: str
    start_frame: int
    end_frame: int
    score: float


def hook_score(energy: float, face: float, question: float, novelty: float) -> float:
    return 0.4 * energy + 0.3 * face + 0.2 * question + 0.1 * novelty


def knapsack_fit(beats: list[Beat], target_frames: int) -> list[Beat]:
    """Drop lowest-score beats until within target (deterministic by score, then id)."""
    ranked = sorted(beats, key=lambda b: (-b.score, b.id))
    chosen = list(ranked)
    while sum(b.end_frame - b.start_frame for b in chosen) > target_frames and len(chosen) > 1:
        chosen.pop()  # lowest score last
    # restore timeline order
    order = {b.id: i for i, b in enumerate(beats)}
    return sorted(chosen, key=lambda b: order[b.id])


def crop_916_params(src_w: int, src_h: int, face_x_center: float | None = None) -> dict:
    """Return {x, w:src_h*9/16 centered on face or middle, y:0, h:src_h} with smoothing note."""
    want_w = int(src_h * 9 / 16)
    want_w = min(want_w, src_w)
    if face_x_center is None:
        x = (src_w - want_w) // 2
    else:
        x = int(min(max(face_x_center * src_w - want_w / 2, 0), src_w - want_w))
    return {"x": x, "y": 0, "w": want_w, "h": src_h, "out_w": 1080, "out_h": 1920}

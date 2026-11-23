"""Shot detection: histogram/mean-abs-diff on frames. cv2 only for file decode.

Classical CV first (cheap, exact): structure with frame diffs, retrieve with
embeddings later. Pure `shot_boundaries` is fully unit-testable with numpy.
"""
from __future__ import annotations


def frame_score(prev, cur) -> float:
    """Normalized mean-abs-diff in [0,1] between two HxWxC uint8 frames."""
    import numpy as np
    a = prev.astype("float32").ravel()
    b = cur.astype("float32").ravel()
    return float(abs(a - b).mean() / 255.0)


def shot_boundaries(frames, threshold: float = 0.25) -> list[int]:
    """Return indices i (1..N-1) where frames[i] starts a new shot."""
    out: list[int] = []
    for i in range(1, len(frames)):
        if frame_score(frames[i - 1], frames[i]) > threshold:
            out.append(i)
    return out


def segments_from_boundaries(n: int, boundaries: list[int]) -> list[tuple[int, int]]:
    """Boundaries -> contiguous [start,end) segments covering [0,n)."""
    cuts = [0, *[b for b in boundaries if 0 < b < n], n]
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1) if cuts[i] < cuts[i + 1]]


def detect_file(path: str, threshold: float = 0.25, max_frames: int = 0) -> dict:
    """Decode with cv2 and return {boundaries, segments, n}. Slow-lane I/O."""
    try:
        import cv2  # type: ignore
    except ImportError as e:
        raise RuntimeError("opencv (cv2) not installed") from e
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()
    boundaries = shot_boundaries(frames, threshold)
    return {"boundaries": boundaries,
            "segments": segments_from_boundaries(len(frames), boundaries),
            "n": len(frames)}

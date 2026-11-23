"""Speaker diarization: pyannote lazy import + pure majority-vote reconcile.

pyannote/speaker-diarization-3.1 is optional (HF token, gated). Never import at
module load; engine treats labels as advisory only.
"""
from __future__ import annotations


def diarize_file(path: str, hf_token: str | None = None) -> list[dict]:
    """Run pyannote 3.1. Raises RuntimeError if missing/tokenless (slow lane only)."""
    try:
        from pyannote.audio import Pipeline  # type: ignore
    except ImportError as e:
        raise RuntimeError("pyannote.audio not installed (optional slow lane)") from e
    import os
    token = hf_token or os.environ.get("HF_TOKEN", "")
    if not token:
        raise RuntimeError("HF_TOKEN missing; will not ask reviewers to supply it")
    pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=token)
    diar = pipe(path)
    return [{"start": float(s.start), "end": float(s.end), "speaker": str(sp)}
            for s, _, sp in diar.itertracks(yield_label=True)]


def reconcile_cues(cues: list[dict], turns: list[dict]) -> list[dict]:
    """Assign each cue the speaker with max overlap. Flag <0.5s turns REVIEW.

    cues: [{start,end,...}], turns: [{start,end,speaker}]. Pure, testable.
    """
    out = []
    for c in cues:
        best, best_ov = None, 0.0
        for t in turns:
            ov = max(0.0, min(c["end"], t["end"]) - max(c["start"], t["start"]))
            if ov > best_ov:
                best, best_ov = t["speaker"], ov
        flag = "REVIEW" if best_ov < 0.5 and best is not None else "OK"
        out.append({**c, "speaker": best, "speaker_overlap": round(best_ov, 3), "flag": flag})
    return out

"""Transcript ingest: JSON words (seconds) -> frame-anchored Words. Plus word-ID resolution."""
from __future__ import annotations

from fractions import Fraction

from .errors import TimelineValidationError
from .schema import Word
from .timebase import t_to_frame


def _sec_to_fraction(x: float | str | Fraction) -> Fraction:
    if isinstance(x, Fraction):
        return x
    return Fraction(str(x))


def ingest_transcript(data: dict, fps_num: int, fps_den: int) -> tuple[Word, ...]:
    """Accept {words:[{word|text, start, end, conf?, speaker?, id?}]} with seconds floats.

    Converts to frame ints via round(t*fps). Assigns stable ids w000001... if missing.
    Raises DANGLING / validation errors on bad ranges.
    """
    raw_words = data.get("words", [])
    out: list[Word] = []
    for i, rw in enumerate(raw_words):
        text = rw.get("word", rw.get("text", ""))
        if not str(text).strip():
            raise TimelineValidationError("EMPTY_WORD", "word text must be non-empty")
        try:
            start_t = _sec_to_fraction(rw["start"])
            end_t = _sec_to_fraction(rw["end"])
        except KeyError as e:
            raise TimelineValidationError("MISSING_TIMESTAMP", f"word missing timestamp: {e}") from e
        sf = t_to_frame(start_t, fps_num, fps_den)
        ef = t_to_frame(end_t, fps_num, fps_den)
        if ef <= sf:
            #word times can collapse after rounding; enforce min 1 frame when end > start in seconds
            if end_t > start_t:
                ef = sf + 1
            else:
                raise TimelineValidationError("ZERO_LENGTH", f"word end must be > start: {rw}")
        wid = rw.get("id") or f"w{i:06d}"
        out.append(
            Word(
                id=wid,
                text=str(text),
                start_frame=sf,
                end_frame=ef,
                conf=float(rw.get("conf", 1.0)),
                speaker=rw.get("speaker"),
            )
        )
    # sort by start
    out.sort(key=lambda w: (w.start_frame, w.id))
    return tuple(out)


def resolve_word_ids(words: tuple[Word, ...], ids: list[str]) -> tuple[int, int]:
    """Resolve [start_id ... end_id] to (start_frame, end_frame) span. Raises DANGLING_WORD_ID."""
    by_id = {w.id: w for w in words}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise TimelineValidationError("DANGLING_WORD_ID", f"unknown word ids: {missing}")
    frames = [by_id[i] for i in ids]
    return min(w.start_frame for w in frames), max(w.end_frame for w in frames)

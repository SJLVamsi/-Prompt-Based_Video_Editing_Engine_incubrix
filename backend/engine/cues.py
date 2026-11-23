"""Words -> subtitle cues + SRT/VTT writers. Pure, no binary."""
from __future__ import annotations

from dataclasses import dataclass

from .schema import Word
from .timebase import frame_to_t


@dataclass(frozen=True)
class Cue:
    start_frame: int
    end_frame: int
    text: str
    speaker: str | None = None


def _fmt_ts_srt(frame: int, fps_num: int, fps_den: int) -> str:
    from fractions import Fraction
    t = Fraction(frame, 1) * Fraction(fps_den, fps_num)
    total_ms = int(round(float(t) * 1000))
    h, rem = divmod(total_ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_ts_vtt(frame: int, fps_num: int, fps_den: int) -> str:
    return _fmt_ts_srt(frame, fps_num, fps_den).replace(",", ".")


def words_to_cues(
    words: tuple[Word, ...] | list[Word],
    fps_num: int,
    fps_den: int,
    min_dur_frames: int = 30,   # ~1s @30fps
    max_dur_frames: int = 180,  # 6s
    max_chars: int = 84,
    lead_frames: int = 3,       # ~100ms
    tail_frames: int = 9,       # ~300ms
    declash_frames: int = 3,    # ~80-100ms
) -> tuple[Cue, ...]:
    """Greedy grouping: break on sentence end, max dur/chars, or gap>=12f (~0.4s)."""
    words = list(words)
    if not words:
        return ()
    cues: list[Cue] = []
    cur: list[Word] = []
    cur_text_len = 0
    for i, w in enumerate(words):
        # reliability flag: skip words with absurd duration? keep but pad later
        cur.append(w)
        cur_text_len += len(w.text) + 1
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt.start_frame - w.end_frame) if nxt else 10**9
        sentence_end = w.text.endswith((".", "!", "?"))
        span = cur[-1].end_frame - cur[0].start_frame
        over = span >= max_dur_frames or cur_text_len >= max_chars
        boundary = sentence_end or gap >= 12 or over or nxt is None
        if boundary:
            s = max(0, cur[0].start_frame - lead_frames)
            e = cur[-1].end_frame + tail_frames
            if e - s < min_dur_frames:
                e = s + min_dur_frames
            text = " ".join(x.text for x in cur)
            # wrap to <=42 chars/line, max 2 lines
            words_txt = text.split()
            lines: list[str] = []
            line = ""
            for wt in words_txt:
                if len(line) + len(wt) + 1 <= 42:
                    line = (line + " " + wt).strip()
                else:
                    lines.append(line)
                    line = wt
            if line:
                lines.append(line)
            if len(lines) > 2:
                # condense: join extras into line 2 truncated
                lines = [lines[0], " ".join(lines[1:])[:42]]
            cues.append(Cue(s, e, "\n".join(lines), speaker=cur[0].speaker))
            cur, cur_text_len = [], 0
    # declash: a.end = min(a.end, b.start - declash)
    fixed: list[Cue] = []
    for i, c in enumerate(cues):
        if i + 1 < len(cues):
            nxt = cues[i + 1]
            e = min(c.end_frame, nxt.start_frame - declash_frames)
            if e <= c.start_frame:
                e = c.start_frame + 1
            fixed.append(Cue(c.start_frame, e, c.text, c.speaker))
        else:
            fixed.append(c)
    return tuple(fixed)


def cues_to_srt(cues: tuple[Cue, ...] | list[Cue], fps_num: int, fps_den: int) -> str:
    out: list[str] = []
    for i, c in enumerate(cues, 1):
        out.append(str(i))
        out.append(f"{_fmt_ts_srt(c.start_frame, fps_num, fps_den)} --> {_fmt_ts_srt(c.end_frame, fps_num, fps_den)}")
        out.append(c.text)
        out.append("")
    return "\n".join(out)


def cues_to_vtt(cues: tuple[Cue, ...] | list[Cue], fps_num: int, fps_den: int) -> str:
    out = ["WEBVTT", ""]
    for c in cues:
        out.append(f"{_fmt_ts_vtt(c.start_frame, fps_num, fps_den)} --> {_fmt_ts_vtt(c.end_frame, fps_num, fps_den)}")
        out.append(c.text)
        out.append("")
    return "\n".join(out)

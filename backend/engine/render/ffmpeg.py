"""ASS generation from cues + ffmpeg cmd builder (no exec in tests)."""
from __future__ import annotations

from .presets import AUDIO, MUX, PRESETS
from .graph import FilterGraph


def cues_to_ass(cues, fps_num: int, fps_den: int) -> str:
    from fractions import Fraction
    def ts(f: int) -> str:
        t = float(Fraction(f, 1) * Fraction(fps_den, fps_num))
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); cs = int(round((t % 1) * 100))
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720",
             "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, BorderStyle, Alignment, MarginV",
             "Style: Default,Inter,20,&HFFFFFF,&H80000000,1,2,30", "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for c in cues:
        text = c.text.replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{ts(c.start_frame)},{ts(c.end_frame)},Default,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"


def build_ffmpeg_cmd(graph: FilterGraph, preset: str = "720p", fps: str = "30",
                     extra_vf_tail: str = "") -> list[str]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset}")
    vf = graph.full + (f",{extra_vf_tail}" if extra_vf_tail else "")
    return (["ffmpeg", "-y", "-fflags", "+genpts", "-i", "src.mp4",
             "-filter_complex", vf, "-map", "[vout]", "-map", "[aout]",
             "-r", fps, "-vsync", "cfr"]
            + PRESETS[preset] + AUDIO + MUX + ["out.mp4"])

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
                     extra_vf_tail: str = "", input_path: str = "src.mp4",
                     output_path: str = "out.mp4") -> list[str]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset}")
    vf = graph.full + (f",{extra_vf_tail}" if extra_vf_tail else "")
    return (["ffmpeg", "-y", "-fflags", "+genpts", "-i", input_path,
             "-filter_complex", vf, "-map", "[vout]", "-map", "[aout]",
             "-r", fps, "-fps_mode", "cfr"]
            + PRESETS[preset] + AUDIO + MUX + [output_path])


def run_cmd(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    """Run ffmpeg; return (returncode, combined stderr+stdout tail). No exception on failure."""
    import subprocess
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    tail = (p.stderr or "")[-4000:]
    return p.returncode, tail


def timeline_captions_to_ass(timeline) -> str:
    """Timeline captions are already output-frame aligned; reuse cues_to_ass."""
    return cues_to_ass(list(timeline.captions), timeline.fps_num, timeline.fps_den)

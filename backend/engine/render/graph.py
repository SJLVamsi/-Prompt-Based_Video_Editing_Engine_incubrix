"""Pure filter-graph builder: Timeline -> graph strings. No subprocess."""
from __future__ import annotations

from dataclasses import dataclass

from ..schema import Timeline
from ..timebase import frame_to_sec_str


@dataclass(frozen=True)
class FilterGraph:
    video_chain: str
    audio_chain: str
    concat_n: int
    full: str


def build_graph(tl: Timeline, fps_num: int | None = None, fps_den: int | None = None) -> FilterGraph:
    fps_num = fps_num or tl.fps_num
    fps_den = fps_den or tl.fps_den
    fps_str = f"{fps_num}/{fps_den}" if fps_den != 1 else f"{fps_num}"
    v_parts: list[str] = []
    a_parts: list[str] = []
    v_labels: list[str] = []
    a_labels: list[str] = []
    for i, clip in enumerate(tl.clips):
        v_in = f"[0:v]" if i == 0 and len(tl.clips) == 1 else f"[vsrc{i}]"
        # split handling emitted by caller; here assume per-clip trim from single input via split upstream
        v = (
            f"{v_in}trim=start_frame={clip.start_frame}:end_frame={clip.end_frame},"
            f"setpts=PTS-STARTPTS"
        )
        if (clip.speed_num, clip.speed_den) != (1, 1):
            factor = clip.speed_den / clip.speed_num
            v += f",setpts={factor}*PTS"
        v += f",fps=fps={fps_str}:round=near[v{i}]"
        v_parts.append(v)
        v_labels.append(f"[v{i}]")
        a0 = frame_to_sec_str(clip.start_frame, tl.fps_num, tl.fps_den)
        a1 = frame_to_sec_str(clip.end_frame, tl.fps_num, tl.fps_den)
        a = f"[0:a]atrim=start={a0}:end={a1},asetpts=PTS-STARTPTS"
        if (clip.speed_num, clip.speed_den) != (1, 1):
            # chain atempo within 0.5-2.0 per stage
            factor = clip.speed_num / clip.speed_den
            stages: list[str] = []
            remaining = factor
            import math
            while remaining > 2.0 + 1e-9:
                stages.append("atempo=2.0")
                remaining /= 2.0
            while remaining < 0.5 - 1e-9:
                stages.append("atempo=0.5")
                remaining /= 0.5
            stages.append(f"atempo={remaining:.6f}")
            a += "," + ",".join(stages)
        a += f",aresample=osr=48000:async=1[a{i}]"
        a_parts.append(a)
        a_labels.append(f"[a{i}]")
    n = len(tl.clips)
    if n == 1:
        v_concat, a_concat = "[v0]format=yuv420p[vout]", "[a0]aformat=sample_fmts=fltp:channel_layouts=stereo[aout]"
    else:
        v_concat = "".join(v_labels) + f"concat=n={n}:v=1:a=0,format=yuv420p[vout]"
        a_concat = "".join(a_labels) + f"concat=n={n}:v=0:a=1,aresample=osr=48000:async=1[aout]"
    # subtitles tail if captions
    if tl.captions:
        v_concat = v_concat.replace("[vout]", "[vcat]") + ";[vcat]subtitles=caps.ass[vout]"
    video_chain = ";".join(v_parts) + ";" + v_concat if v_parts else v_concat
    audio_chain = ";".join(a_parts) + ";" + a_concat if a_parts else a_concat
    full = video_chain + ";" + audio_chain
    return FilterGraph(video_chain=video_chain, audio_chain=audio_chain, concat_n=n, full=full)

"""ffprobe helpers: duration, streams, start offsets. I/O boundary."""
from __future__ import annotations

import json
import subprocess


def probe(path: str) -> dict:
    cmd = ["ffprobe", "-v", "error",
           "-show_entries", "format=duration,size",
           "-show_entries", "stream=index,codec_type,codec_name,r_frame_rate,avg_frame_rate,time_base,nb_frames,duration,start_time,width,height,sample_rate",
           "-of", "json", path]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {p.stderr[-1000:]}")
    return json.loads(p.stdout)


def summarize(path: str) -> dict:
    info = probe(path)
    duration = float(info.get("format", {}).get("duration", 0.0))
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {})
    v_start = float(video.get("start_time", 0.0) or 0.0)
    a_start = float(audio.get("start_time", 0.0) or 0.0)
    return {
        "duration": duration,
        "nb_frames": int(video.get("nb_frames", 0) or 0),
        "r_frame_rate": video.get("r_frame_rate"),
        "avg_frame_rate": video.get("avg_frame_rate"),
        "v_start": v_start,
        "a_start": a_start,
        "av_offset": abs(v_start - a_start),
    }

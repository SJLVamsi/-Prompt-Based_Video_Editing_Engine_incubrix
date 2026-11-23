"""Slow render evidence: synthetic testsrc+sine, 23.976, VFR normalize.

Requires ffmpeg/ffprobe binaries. Skipped when missing (fast lane stays green).
Run: pytest -m slow  (or pytest backend/tests/test_sync_slow.py)
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from backend.engine.ops.cut import op_cut
from backend.engine.render.ffmpeg import build_ffmpeg_cmd, run_cmd
from backend.engine.render.graph import build_graph
from backend.engine.render.probe import summarize
from backend.engine.schema import Clip, create_timeline

HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_ffmpeg = pytest.mark.skipif(not HAVE_FFMPEG, reason="ffmpeg/ffprobe missing")


def _run(cmd: list[str], timeout: int = 180) -> None:
    rc, tail = run_cmd(cmd, timeout=timeout)
    assert rc == 0, f"cmd failed rc={rc}: {' '.join(cmd[:6])}...\n{tail[-2000:]}"


def _gen_cfr(tmp: Path, name: str = "src.mp4", dur: int = 10,
             rate: str = "30", size: str = "320x240") -> Path:
    out = tmp / name
    _run(["ffmpeg", "-y",
          "-f", "lavfi", "-i", f"testsrc=duration={dur}:size={size}:rate={rate}",
          "-f", "lavfi", "-i", f"sine=frequency=1000:duration={dur}:sample_rate=48000",
          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000",
          "-shortest", str(out)])
    return out


@needs_ffmpeg
def test_cfr_length_and_av_offset(tmp_path):
    src = _gen_cfr(tmp_path)
    tl = create_timeline(30, 1, [Clip("c1", "src", 0, 300)])
    # keep [60,300): cut head 0..60 -> expect 240 frames / 8.0s
    out_tl = op_cut(tl, [(0, 60)])
    assert out_tl.duration_frames == 240
    g = build_graph(out_tl)
    assert "trim=start_frame=60:end_frame=300" in g.full
    out = tmp_path / "out.mp4"
    cmd = build_ffmpeg_cmd(g, preset="preview", fps="30",
                           input_path=str(src), output_path=str(out))
    _run(cmd)
    s = summarize(str(out))
    assert abs(s["duration"] - 8.0) < 0.15, s  # ~1.5 frames @30fps = 0.05s; lavfi headroom 0.15
    assert s["av_offset"] < 0.04, s


@needs_ffmpeg
def test_23976_roundtrip_frames(tmp_path):
    dur = 6
    src = _gen_cfr(tmp_path, name="src23976.mp4", dur=dur, rate="24000/1001", size="320x240")
    tl = create_timeline(24000, 1001, [Clip("c1", "src", 0, 144)])
    g = build_graph(tl)
    out = tmp_path / "out23976.mp4"
    cmd = build_ffmpeg_cmd(g, preset="preview", fps="24000/1001",
                           input_path=str(src), output_path=str(out))
    _run(cmd)
    s = summarize(str(out))
    # 144 frames @24000/1001 = 6.006s
    assert abs(s["duration"] - 6.006) < 0.10, s
    assert s["av_offset"] < 0.04, s


@needs_ffmpeg
def test_vfr_phone_normalizes_to_cfr(tmp_path):
    # Simulate VFR phone: encode with vsync vfr from a CFR lavfi source
    cfr = _gen_cfr(tmp_path, name="cfr.mp4", dur=6)
    vfr = tmp_path / "vfr.mp4"
    _run(["ffmpeg", "-y", "-i", str(cfr), "-fps_mode", "vfr", "-c:v", "libx264",
          "-pix_fmt", "yuv420p", "-c:a", "aac", str(vfr)])
    tl = create_timeline(30, 1, [Clip("c1", "src", 0, 180)])
    g = build_graph(tl)
    # graph must contain CFR normalization
    assert "fps=fps=30" in g.full and "aresample" in g.full
    out = tmp_path / "outvfr.mp4"
    cmd = build_ffmpeg_cmd(g, preset="preview", fps="30",
                           input_path=str(vfr), output_path=str(out))
    _run(cmd)
    s = summarize(str(out))
    assert abs(s["duration"] - 6.0) < 0.15, s

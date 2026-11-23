"""Scene detection: pure numpy unit + real ffmpeg-generated cut (needs cv2+ffmpeg)."""
import shutil

import pytest

from backend.engine.scene import frame_score, segments_from_boundaries, shot_boundaries

np = pytest.importorskip("numpy", reason="numpy missing")


def _solid(h=8, w=8, v=0):
    return np.full((h, w, 3), v, dtype="uint8")


def test_abrupt_cut_detected():
    frames = [_solid(v=10)] * 5 + [_solid(v=200)] * 5
    assert shot_boundaries(frames) == [5]


def test_identical_frames_no_boundary():
    assert shot_boundaries([_solid(v=7)] * 10) == []


def test_fade_below_threshold_ignored():
    frames = [_solid(v=i * 2) for i in range(10)]  # gradual ramp, max step 2/255
    assert shot_boundaries(frames, threshold=0.25) == []
    assert shot_boundaries(frames, threshold=0.001) != []


def test_segments_cover_range():
    assert segments_from_boundaries(10, [5]) == [(0, 5), (5, 10)]
    assert segments_from_boundaries(10, []) == [(0, 10)]


def test_real_cut_in_generated_video(tmp_path):
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg missing")
    import subprocess
    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    joined = tmp_path / "j.mp4"
    for out, color in ((a, "red"), (b, "blue")):
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                            "-i", f"color=c={color}:s=64x64:r=30:d=2",
                            "-pix_fmt", "yuv420p", str(out)],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-300:]
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(a), "-i", str(b),
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]",
                        str(joined)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-300:]
    from backend.engine.scene import detect_file
    try:
        res = detect_file(str(joined), threshold=0.25)
    except RuntimeError as e:
        pytest.skip(str(e))
    assert res["n"] == 120, res
    assert len(res["boundaries"]) == 1
    assert abs(res["boundaries"][0] - 60) <= 2, res

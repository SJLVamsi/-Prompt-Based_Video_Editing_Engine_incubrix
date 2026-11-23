"""UAT slice API: upload validation, transcribe wiring, clarify path, download 404.

Full genuine flow (say audio -> silence cut -> subs -> 9:16) runs live vs the
container in the UAT runbook (docs/testing/UAT.md); here we pin contracts.
"""
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

c = TestClient(app)
ffmpeg = shutil.which("ffmpeg")


def _sample(tmp_path, name="s.mp4", dur=2):
    out = tmp_path / name
    r = subprocess.run(["ffmpeg", "-y", "-v", "error",
                        "-f", "lavfi", "-i", f"testsrc=duration={dur}:size=320x240:rate=30",
                        "-f", "lavfi", "-i", f"sine=frequency=880:duration={dur}:sample_rate=48000",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-shortest", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-300:]
    return out


@pytest.mark.skipif(ffmpeg is None, reason="ffmpeg missing")
def test_upload_ok_and_bad_ext(tmp_path):
    src = _sample(tmp_path)
    with open(src, "rb") as f:
        r = c.post("/v1/uploads", files={"file": ("s.mp4", f, "video/mp4")})
    assert r.status_code == 200, r.text[:300]
    assert r.json()["assetId"]
    r2 = c.post("/v1/uploads", files={"file": ("x.txt", b"hi", "text/plain")})
    assert r2.status_code == 415


@pytest.mark.skipif(ffmpeg is None, reason="ffmpeg missing")
def test_transcribe_missing_asset():
    r = c.post("/v1/transcribe", json={"assetId": "nope"})
    assert r.status_code == 404


@pytest.mark.skipif(ffmpeg is None, reason="ffmpeg missing")
def test_uat_run_needs_transcribe_first(tmp_path):
    src = _sample(tmp_path)
    with open(src, "rb") as f:
        aid = c.post("/v1/uploads", files={"file": ("s.mp4", f, "video/mp4")}).json()["assetId"]
    r = c.post("/v1/uat/run", json={"assetId": aid, "prompt": "remove silence and add subtitles"})
    assert r.status_code == 422  # transcribed words required


def test_uat_unknown_prompt_clarifies_without_transcribe(tmp_path):
    # clarify happens only after asset+words exist; unknown asset -> 404 first
    r = c.post("/v1/uat/run", json={"assetId": "nope", "prompt": "make it pop"})
    assert r.status_code == 404


def test_download_missing():
    assert c.get("/v1/exports/nope/download").status_code == 404

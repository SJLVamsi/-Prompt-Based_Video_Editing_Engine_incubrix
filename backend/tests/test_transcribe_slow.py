"""Transcribe slow lane: faster-whisper tiny + VAD.

- Silence (anullsrc 3s) with VAD filter -> expect ~0 words (no hallucination leak).
- Speech via macOS `say` (if present) -> tiny model should return >=1 word.
Skipped when faster-whisper missing. Model downloads on first run (~75MB tiny).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

fw = pytest.importorskip("faster_whisper", reason="faster-whisper missing")

from backend.engine.transcribe import transcribe_file  # noqa: E402


def _wav_silence(path: Path, secs: int = 3) -> Path:
    r = subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        f"anullsrc=r=16000:cl=mono:d={secs}",
                        "-ar", "16000", "-ac", "1", str(path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]
    return path


def test_silence_vad_no_hallucination(tmp_path):
    wav = _wav_silence(tmp_path / "sil.wav")
    res = transcribe_file(str(wav), model="tiny",
                          vad={"threshold": 0.5, "min_silence_duration_ms": 500,
                               "speech_pad_ms": 400})
    assert len(res.words) <= 2, res.words  # VAD must suppress silence hallucinations


def test_say_speech_transcribes(tmp_path):
    if shutil.which("say") is None:
        pytest.skip("macOS say missing")
    aiff = tmp_path / "sp.aiff"
    wav = tmp_path / "sp.wav"
    r = subprocess.run(["say", "-v", "Samantha", "-o", str(aiff),
                        "hello demo captions today"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("say failed")
    r2 = subprocess.run(["ffmpeg", "-y", "-i", str(aiff), "-ar", "16000",
                         "-ac", "1", str(wav)], capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr[-500:]
    res = transcribe_file(str(wav), model="tiny")
    assert len(res.words) >= 1, res.words

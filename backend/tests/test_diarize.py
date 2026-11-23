"""Diarize reconcile (pure) + graceful missing-dep behavior."""
import pytest

from backend.engine.diarize import diarize_file, reconcile_cues


def test_reconcile_majority_vote():
    cues = [{"start": 0.0, "end": 2.0, "text": "hi"},
            {"start": 2.0, "end": 4.0, "text": "yo"}]
    turns = [{"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00"},
             {"start": 2.0, "end": 4.0, "speaker": "SPEAKER_01"}]
    out = reconcile_cues(cues, turns)
    assert out[0]["speaker"] == "SPEAKER_00"
    assert out[1]["speaker"] == "SPEAKER_01"
    assert all(r["flag"] == "OK" for r in out)


def test_short_turn_flagged_review():
    cues = [{"start": 5.0, "end": 5.3, "text": "yeah"}]
    turns = [{"start": 5.0, "end": 5.3, "speaker": "SPEAKER_01"}]
    out = reconcile_cues(cues, turns)
    assert out[0]["flag"] == "REVIEW"  # <0.5s overlap backchannel


def test_missing_dep_raises_clean():
    try:
        import pyannote.audio  # noqa: F401
        pytest.skip("pyannote installed; slow lane")
    except ImportError:
        with pytest.raises(RuntimeError, match="pyannote"):
            diarize_file("nope.wav", hf_token="x")

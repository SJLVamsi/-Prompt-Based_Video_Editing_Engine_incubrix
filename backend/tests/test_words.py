"""Transcript ingest + word-id resolution."""
import pytest

from backend.engine.errors import TimelineValidationError
from backend.engine.words import ingest_transcript, resolve_word_ids


def test_ingest_frames():
    data = {"words": [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.5, "end": 1.0, "speaker": "SPEAKER_01"},
    ]}
    words = ingest_transcript(data, 30, 1)
    assert words[0].start_frame == 0 and words[0].end_frame == 15
    assert words[1].start_frame == 15 and words[1].end_frame == 30
    assert words[0].id == "w000000"


def test_dangling_id():
    words = ingest_transcript({"words": [{"word": "a", "start": 0, "end": 1}]}, 30, 1)
    with pytest.raises(TimelineValidationError) as e:
        resolve_word_ids(words, ["nope"])
    assert e.value.code == "DANGLING_WORD_ID"


def test_retiming_preserves_intent():
    base = {"words": [{"id": "w1", "word": "hi", "start": 1.0, "end": 1.5}]}
    w1 = ingest_transcript(base, 30, 1)
    # ±2 frames shift in seconds (~66ms) keeps same id, span shifts slightly
    shifted = {"words": [{"id": "w1", "word": "hi", "start": 1.02, "end": 1.52}]}
    w2 = ingest_transcript(shifted, 30, 1)
    assert w2[0].id == "w1"
    assert abs(w2[0].start_frame - w1[0].start_frame) <= 2
    s, e = resolve_word_ids(w2, ["w1"])
    assert (s, e) == (w2[0].start_frame, w2[0].end_frame)

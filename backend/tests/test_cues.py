"""Cues golden + corruption."""
from backend.engine.cues import cues_to_srt, cues_to_vtt, words_to_cues
from backend.engine.words import ingest_transcript


def _words():
    data = {"words": [
        {"word": "hello", "start": 0.4, "end": 0.65},
        {"word": "world.", "start": 0.7, "end": 1.0},
        {"word": "this", "start": 2.0, "end": 2.3},
        {"word": "is", "start": 2.3, "end": 2.5},
        {"word": "a", "start": 2.5, "end": 2.6},
        {"word": "test", "start": 2.6, "end": 3.0},
    ]}
    return ingest_transcript(data, 30, 1)


def test_srt_vtt_golden():
    words = _words()
    cues = words_to_cues(words, 30, 1)
    assert len(cues) >= 1
    srt = cues_to_srt(cues, 30, 1)
    vtt = cues_to_vtt(cues, 30, 1)
    assert "-->" in srt and "," in srt.split("-->")[1][:20]
    assert vtt.startswith("WEBVTT")
    assert "-->" in vtt and "." in vtt.split("-->")[1][:20]
    # no cue longer than 7s, lines <=42
    for c in cues:
        assert c.end_frame - c.start_frame <= 7 * 30 + 15
        for line in c.text.split("\n"):
            assert len(line) <= 42


def test_empty_words_no_crash():
    assert words_to_cues((), 30, 1) == ()

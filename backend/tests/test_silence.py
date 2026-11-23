"""Word-gap silence math + preview args."""
from backend.engine.silence import silencedetect_preview_args, word_gap_cuts
from backend.engine.words import ingest_transcript


def test_gap_math():
    words = ingest_transcript({"words": [
        {"word": "a", "start": 0.0, "end": 1.0},
        {"word": "b", "start": 2.0, "end": 3.0},  # 1.0s gap @30fps = 30f
    ]}, 30, 1)
    cuts = word_gap_cuts(words, 30, 1, min_gap_sec=0.5, target_gap_sec=0.3)
    assert len(cuts) == 1
    cs, ce = cuts[0]
    assert (ce - cs) == 30 - 9  # excess removed, 9f target remains
    # remaining gap == 9 frames
    assert (words[1].start_frame - words[0].end_frame) - (ce - cs) == 9


def test_short_gap_ignored():
    words = ingest_transcript({"words": [
        {"word": "a", "start": 0.0, "end": 1.0},
        {"word": "b", "start": 1.2, "end": 2.0},  # 0.2s gap
    ]}, 30, 1)
    assert word_gap_cuts(words, 30, 1) == []


def test_preview_args():
    args = silencedetect_preview_args()
    assert "silencedetect" in args[1]

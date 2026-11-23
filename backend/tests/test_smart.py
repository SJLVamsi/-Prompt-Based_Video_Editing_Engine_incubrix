"""LLM/session/shorts/search pure tests."""
from backend.engine.shorts import crop_916_params, hook_score, knapsack_fit, Beat
from backend.engine.search import keyword_search


def test_hook_and_fit():
    assert hook_score(1, 1, 1, 1) == __import__("pytest").approx(1.0)
    beats = [Beat("b1", 0, 100, 0.9), Beat("b2", 100, 500, 0.1), Beat("b3", 500, 600, 0.8)]
    chosen = knapsack_fit(beats, 250)
    assert sum(b.end_frame - b.start_frame for b in chosen) <= 250
    assert chosen[0].id == "b1"


def test_crop_center():
    p = crop_916_params(1920, 1080)
    assert p["out_w"] == 1080 and p["h"] == 1080


def test_keyword_search():
    segs = [{"start": 1.0, "end": 3.0, "text": "pricing explained here"},
            {"start": 10.0, "end": 12.0, "text": "unrelated cats"}]
    hits = keyword_search("where is pricing explained", segs)
    assert hits and hits[0].t == 1.0

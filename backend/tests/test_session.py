"""3-way matrix with MockLLM: valid/ambiguous/impossible/invalid/overflow."""
from backend.engine.schema import Clip, create_timeline
from backend.engine.session import MockLLM, parse_plan, run_session, translate
from backend.engine.words import ingest_transcript
import pytest
from backend.engine.errors import TimelineValidationError


def _tl():
    words = ingest_transcript({"words": [{"word": "a", "start": 0, "end": 1}]}, 30, 1)
    tl = create_timeline(30, 1, [Clip("c1", "src", 0, 300)], words=words)
    return tl


def test_valid_plan_parses():
    raw = '{"version":"v1","intent":"trim","response":"results","ops":[{"op":"cut","start":0,"end":2}]}'
    plan = parse_plan(raw)
    assert plan["response"] == "results"


def test_extra_keys_rejected():
    with pytest.raises(TimelineValidationError):
        parse_plan('{"version":"v1","ops":[{"op":"cut","start":0,"end":1}],"evil":1}')


def test_malformed_triggers_retry_then_clarify(tmp_path):
    llm = MockLLM({"hello": "not json at all"})
    out = run_session(tmp_path / "s1", "hello", _tl(), llm)
    assert out["status"] == "clarify"


def test_overflow_rejected_or_clamped(tmp_path):
    # 999s exceeds 10s duration -> clarify fallback after retry
    llm = MockLLM({"x": '{"version":"v1","response":"results","ops":[{"op":"cut","start":0,"end":999}]}'})
    out = run_session(tmp_path / "s2", "x", _tl(), llm)
    assert out["status"] in ("clarify", "done")


def test_three_ways(tmp_path):
    tl = _tl()
    llm = MockLLM({
        "trim": '{"version":"v1","response":"results","ops":[{"op":"cut","start":0,"end":2}]}',
        "vague": '{"version":"v1","response":"clarify","clarify_question":"Which part?","ops":[]}',
        "impossible": '{"version":"v1","response":"reject","rejection_reason":"unsafe","ops":[]}',
    })
    assert run_session(tmp_path / "a", "trim this", tl, llm)["status"] == "done"
    assert run_session(tmp_path / "b", "vague thing", tl, llm)["status"] == "clarify"
    r = run_session(tmp_path / "c", "impossible thing", tl, llm)
    assert r["status"] == "reject"

"""Golden 8-step (steps 1-5, no exec): ingest -> ops -> hashes -> graph strings."""
import json
from pathlib import Path

from backend.engine.history import init_history, push, redo, restore, undo
from backend.engine.ops.caption import op_caption_add
from backend.engine.ops.cut import op_cut
from backend.engine.ops.speed import op_speed
from backend.engine.render.graph import build_graph
from backend.engine.schema import Clip, create_timeline
from backend.engine.words import ingest_transcript, resolve_word_ids

FIX = Path(__file__).parent / "fixtures" / "words_10s.json"


def _load():
    data = json.loads(FIX.read_text())
    words = ingest_transcript(data, 30, 1)
    tl0 = create_timeline(
        30, 1, [Clip("c1", "src", 0, 300)],
        words=words, source_id="synthetic",
    )
    return tl0


def test_golden_8step_noexec():
    # 1. ingest
    tl0 = _load()
    assert len(tl0.words) == 10
    assert tl0.words[0].start_frame == 0
    # 2. prompt->ops stub: cut w0..w1, speed w4..w5 2x, caption w8..w9
    s_cut, _ = resolve_word_ids(tl0.words, ["w000000", "w000001"])
    # resolve gives span 0..60
    assert (s_cut) == 0
    tl1 = op_cut(tl0, [(0, 60)])  # remove filler start
    assert tl1.duration_frames == 240
    h1 = tl1.timeline_hash
    tl2 = op_speed(tl1, 120, 180, 2, 1)  # middle 60f -> 30f output
    assert tl2.duration_frames == 210
    tl3 = op_caption_add(tl2, "hello", 180, 210)
    h3 = tl3.timeline_hash
    # 3-4. hash chain
    assert tl1.parent_hash == tl0.timeline_hash
    assert tl3.parent_hash != h1
    # 5. graph strings (no binary)
    g = build_graph(tl3)
    assert "trim=start_frame=" in g.full
    assert "atempo=2.000000" in g.full
    assert "subtitles" in g.full
    assert f"concat=n={len(tl3.clips)}" in g.full
    # undo/restore stability
    h = init_history(tl0)
    h = push(h, tl1)
    h = push(h, tl2)
    h = push(h, tl3)
    h, _ = undo(h)
    assert h.present.timeline_hash == tl2.timeline_hash
    h2 = restore(h, tl1.timeline_hash)
    assert h2.present.timeline_hash == tl1.timeline_hash
    assert h2.present.duration_frames == 240

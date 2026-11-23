"""Conversational 4-turn: refine -> undo -> hook-as-keep -> restore. Hash-stable."""
from backend.engine.history import init_history, push, redo, restore, undo
from backend.engine.ops.cut import op_cut
from backend.engine.ops.keep import op_keep
from backend.engine.schema import Clip, create_timeline


def _base():
    return create_timeline(30, 1, [Clip("c1", "src", 0, 300)])


def test_conversational_4turn():
    # T1 refine: tighten intro (cut head)
    h = init_history(_base())
    t1 = op_cut(h.present, [(0, 30)])
    h = push(h, t1)
    # T2 undo that cut
    h, did = undo(h)
    assert not did and h.present.duration_frames == 300
    # redo to get back
    h, did = redo(h)
    assert h.present.duration_frames == 270
    # T3 hook: keep demo region as new branch (keep is deterministic)
    hook = op_keep(h.present, [(60, 210)])
    h_hook = push(h, hook)
    assert h_hook.present.duration_frames == 150
    # T4 restore version 1 (post-cut): replay gives identical hash
    restored = restore(h_hook, t1.timeline_hash)
    assert restored.present.timeline_hash == t1.timeline_hash
    assert restored.present.duration_frames == 270
    # undo of restore returns to hook state (restore is undoable)
    back, _ = undo(restored)
    assert back.present.timeline_hash == hook.timeline_hash

"""History: undo chain, redo, unknown restore."""
import pytest

from backend.engine.errors import TimelineValidationError
from backend.engine.history import init_history, push, redo, restore, undo
from backend.engine.ops.caption import op_caption_add
from backend.engine.ops.cut import op_cut
from backend.engine.schema import Clip, create_timeline


def _base():
    return create_timeline(30, 1, [Clip("c1", "src", 0, 300)])


def test_undo_redo_chain():
    h = init_history(_base())
    hashes = [h.present.timeline_hash]
    cur = h.present
    for i in range(5):
        cur = op_caption_add(cur, f"t{i}", 10 + i * 10, 20 + i * 10)
        h = push(h, cur)
        hashes.append(cur.timeline_hash)
    for _ in range(5):
        h, did = undo(h)
        assert not did
    assert h.present.timeline_hash == hashes[0]
    for _ in range(5):
        h, did = redo(h)
        assert not did
    assert h.present.timeline_hash == hashes[-1]


def test_restore_unknown_raises():
    h = init_history(_base())
    with pytest.raises(TimelineValidationError) as e:
        restore(h, "deadbeef")
    assert e.value.code == "NOT_FOUND"


def test_restore_is_undoable():
    h = init_history(_base())
    mid = op_cut(h.present, [(0, 30)])
    h = push(h, mid)
    late = op_cut(h.present, [(60, 90)])
    h = push(h, late)
    h2 = restore(h, h.past[0].timeline_hash if hasattr(h.past[0], "timeline_hash") else h.snapshots and list(h.snapshots)[0])
    # undoable: undo returns to late
    h3, did = undo(h2)
    assert not did
    assert h3.present.timeline_hash == late.timeline_hash

"""Hash stability: key order, restarts, caption mutation."""
from backend.engine.schema import Clip, create_timeline
from backend.engine.ops.caption import op_caption_add
from backend.engine.store import load_timeline, save_timeline, timeline_to_dict
from backend.engine.schema import Timeline, Caption, SourceFingerprint
from backend.engine.hash import compute_timeline_hash


def _tl():
    return create_timeline(30, 1, [Clip("c1", "src", 0, 300)])


def test_hash_stable(tmp_path):
    a = _tl()
    b = _tl()
    assert a.timeline_hash == b.timeline_hash
    # save/load round-trip stable
    p = tmp_path / "tl.json"
    save_timeline(a, p)
    c = load_timeline(p)
    assert c.timeline_hash == a.timeline_hash
    assert timeline_to_dict(c)["timeline_hash"] == a.timeline_hash


def test_caption_changes_hash():
    a = _tl()
    b = op_caption_add(a, "hello", 30, 60)
    assert b.timeline_hash != a.timeline_hash
    # re-create same caption with same id -> same hash
    c = op_caption_add(a, "hello", 30, 60, caption_id=b.captions[0].id)
    assert c.timeline_hash == b.timeline_hash

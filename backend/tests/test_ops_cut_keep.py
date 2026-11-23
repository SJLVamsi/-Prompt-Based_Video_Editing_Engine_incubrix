"""cut/keep complement, edges, fuzz."""
import pytest

from backend.engine.errors import TimelineValidationError
from backend.engine.ops.cut import op_cut
from backend.engine.ops.keep import op_keep
from backend.engine.ops.ranges import complement_ranges
from backend.engine.schema import Clip, create_timeline


def _tl(frames=300):
    return create_timeline(30, 1, [Clip("c1", "src", 0, frames)])


def test_empty_cut_noop():
    tl = _tl()
    out = op_cut(tl, [])
    assert out is tl
    assert out.timeline_hash == tl.timeline_hash


def test_zero_length_raises():
    tl = _tl()
    with pytest.raises(TimelineValidationError) as e:
        op_cut(tl, [(10, 10)])
    assert e.value.code == "ZERO_LENGTH"


def test_full_cut_raises():
    tl = _tl(100)
    with pytest.raises(TimelineValidationError) as e:
        op_cut(tl, [(0, 100)])
    assert e.value.code == "EMPTY_TIMELINE"


def test_overlap_coalesced():
    tl = _tl(100)
    out = op_cut(tl, [(10, 30), (20, 40)])
    spans = [(c.start_frame, c.end_frame) for c in out.clips]
    assert spans == [(0, 10), (40, 100)]


def test_keep_complement_fuzz():
    for duration in (60, 120, 300):
        tl = _tl(duration)
        keeps = [(10, 50), (70, 100)] if duration >= 100 else [(5, duration - 5)]
        kept = op_keep(tl, keeps)
        cut = op_cut(tl, complement_ranges(keeps, duration))
        assert [(c.start_frame, c.end_frame) for c in kept.clips] == [
            (c.start_frame, c.end_frame) for c in cut.clips
        ]


def test_keep_empty_raises():
    tl = _tl()
    with pytest.raises(TimelineValidationError):
        op_keep(tl, [])

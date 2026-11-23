"""speed + caption edge cases."""
import pytest

from backend.engine.errors import TimelineValidationError
from backend.engine.ops.caption import op_caption_add
from backend.engine.ops.speed import op_speed
from backend.engine.schema import Clip, create_timeline


def _tl():
    return create_timeline(30, 1, [Clip("c1", "src", 0, 300)])


def test_bad_speed():
    tl = _tl()
    with pytest.raises(TimelineValidationError) as e:
        op_speed(tl, 0, 60, 0, 1)
    assert e.value.code == "BAD_SPEED"
    with pytest.raises(TimelineValidationError):
        op_speed(tl, 0, 60, 1, 0)


def test_speed_rescales_caption_inside():
    tl = op_caption_add(_tl(), "hi", 120, 150)
    out = op_speed(tl, 120, 180, 2, 1)
    cap = [c for c in out.captions if c.text == "hi"][0]
    # 30f span at 2x -> 15f
    assert cap.end_frame - cap.start_frame == 15
    assert cap.start_frame == 120


def test_caption_duplicate_rejected():
    tl = op_caption_add(_tl(), "hi", 10, 40)
    with pytest.raises(TimelineValidationError) as e:
        op_caption_add(tl, "hi", 10, 40)
    assert e.value.code == "DUPLICATE_CAPTION"


def test_caption_empty_rejected():
    with pytest.raises(TimelineValidationError):
        op_caption_add(_tl(), "   ", 10, 40)

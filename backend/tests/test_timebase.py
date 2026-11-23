"""Frame math: 24000/1001 vectors, round-trips, float-naive drift demo."""
from fractions import Fraction

from backend.engine.timebase import frame_to_t, parse_r_frame_rate, t_to_frame


def test_23976_vector():
    # frame 144 @24000/1001 -> exactly 6.006s (144*1001/24000)
    t = frame_to_t(144, 24000, 1001)
    assert t == Fraction(144144, 24000) == Fraction(6006, 1000)
    assert abs(float(t) - 6.006) < 1e-9
    assert t_to_frame(t, 24000, 1001) == 144


def test_roundtrip_10k():
    for f in range(0, 10000, 7):
        t = frame_to_t(f, 30000, 1001)
        assert t_to_frame(t, 30000, 1001) == f
    for f in range(0, 300):
        t = frame_to_t(f, 30, 1)
        assert t_to_frame(t, 30, 1) == f


def test_float_naive_off_by_one_demo():
    # Document why floats drift: truncated 23.976 (3dp) vs exact 24000/1001,
    # plus binary float accumulation (0.1+0.2 != 0.3).
    fps_truncated = 23.976
    fps_exact = Fraction(24000, 1001)
    assert abs(fps_truncated - float(fps_exact)) > 1e-9
    # binary float accumulation drifts: classic 0.1+0.2 != 0.3
    assert (0.1 + 0.2) != 0.3
    assert Fraction(1, 10) + Fraction(2, 10) == Fraction(3, 10)
    # int() truncation vs round() disagree on .5 boundaries
    assert int(5.5) != round(5.5)
    assert parse_r_frame_rate("30000/1001") == (30000, 1001)
    assert parse_r_frame_rate("30") == (30, 1)

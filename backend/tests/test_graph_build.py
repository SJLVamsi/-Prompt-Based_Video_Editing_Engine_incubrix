"""Graph builder asserts (no binary)."""
from backend.engine.render.graph import build_graph
from backend.engine.schema import Clip, create_timeline


def test_graph_build():
    tl = create_timeline(30, 1, [
        Clip("c1", "src", 60, 300),
        Clip("c2", "src", 300, 360, speed_num=2, speed_den=1),
    ])
    g = build_graph(tl)
    assert "trim=start_frame=60:end_frame=300" in g.full
    assert "atempo=2.000000" in g.full
    assert "concat=n=2" in g.full
    assert g.concat_n == 2

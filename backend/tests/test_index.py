"""Embedding index: determinism, KNN relevance, SQLite persistence, RRF fusion."""
import math

from backend.engine.index import (
    Chunk, EmbeddingIndex, embed_text, fuse_on_timeline,
)


def test_embed_deterministic_normalized():
    a, b = embed_text("pricing explained here"), embed_text("pricing explained here")
    assert a == b
    assert abs(math.sqrt(sum(v * v for v in a)) - 1.0) < 1e-9
    assert embed_text("pricing") != embed_text("cats")


def test_add_query_relevance():
    idx = EmbeddingIndex()
    idx.add([
        Chunk("c1", "transcript", 1.0, 3.0, "pricing explained here"),
        Chunk("c2", "transcript", 10.0, 12.0, "unrelated cats playing"),
    ])
    hits = idx.query("where is pricing explained", k=2)
    assert hits[0]["id"] == "c1"
    assert hits[0]["score"] > hits[1]["score"]


def test_persistence_across_reopen(tmp_path):
    db = tmp_path / "idx.sqlite"
    idx = EmbeddingIndex(db)
    idx.add([Chunk("c1", "transcript", 1.0, 3.0, "pricing explained here")])
    idx2 = EmbeddingIndex(db)
    hits = idx2.query("pricing", k=1)
    assert hits and hits[0]["id"] == "c1"


def test_modality_filter():
    idx = EmbeddingIndex()
    idx.add([Chunk("t1", "transcript", 1.0, 2.0, "demo hook"),
             Chunk("v1", "visual", 1.0, 2.0, "demo hook")])
    assert {h["modality"] for h in idx.query("demo hook", modality="visual")} == {"visual"}


def test_fuse_weights_and_why():
    text = [{"video_id": "v0", "start": 247.0, "score": 0.98}]
    vis = [{"video_id": "v0", "start": 248.0, "score": 0.31}]
    out = fuse_on_timeline(text, vis, w_text=0.6, w_vis=0.4)
    assert out[0]["t"] == 245.0  # 5s bucket
    assert out[0]["score"] == 0.6 * 0.98 + 0.4 * 0.31
    assert out[0]["why"] == {"text": 0.98, "visual": 0.31}

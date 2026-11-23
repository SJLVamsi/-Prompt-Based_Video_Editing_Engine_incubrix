"""Local vector index: deterministic hashed embeddings + SQLite persistence.

MVP encoders are dependency-free and offline (hashed bag-of-words, L2-normed).
Swap `embed_text`/`embed_image` with BGE/CLIP later — the store, KNN, and
timeline-bucket fusion below stay unchanged (dim is versioned per table).

Roadmap: sqlite-vec (ANN) or Chroma when >100k vectors; pgvector only when
Postgres is already the system of record.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DIM = 256
TABLE = "embeddings_v1_hash256"
_TOKEN = re.compile(r"[a-z0-9]+")


def embed_text(text: str, dim: int = DIM) -> list[float]:
    """Deterministic hashed token embedding, L2-normalized. No weights, no network."""
    vec = [0.0] * dim
    for tok in _TOKEN.findall(text.lower()):
        h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
        vec[(h >> 17) % dim] += 0.5
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass
class Chunk:
    id: str
    modality: str  # transcript | visual
    start: float
    end: float
    text: str | None = None
    vector: list[float] | None = None


class EmbeddingIndex:
    """SQLite-backed (stdlib) vector store: exact cosine KNN + metadata filter."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.db = sqlite3.connect(str(path))
        self.db.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE}
                (id TEXT PRIMARY KEY, modality TEXT, start REAL, end REAL,
                 text TEXT, vector TEXT)"""
        )

    def add(self, chunks: list[Chunk]) -> None:
        rows = [(c.id, c.modality, c.start, c.end, c.text,
                 json.dumps(c.vector or embed_text(c.text or "")))
                for c in chunks]
        self.db.executemany(
            f"INSERT OR REPLACE INTO {TABLE}(id,modality,start,end,text,vector) VALUES (?,?,?,?,?,?)",
            rows)
        self.db.commit()

    def query(self, text: str, k: int = 10, modality: str | None = None) -> list[dict]:
        q = embed_text(text)
        sql = f"SELECT id,modality,start,end,text,vector FROM {TABLE}"
        args: tuple = ()
        if modality:
            sql += " WHERE modality=?"
            args = (modality,)
        scored = []
        for cid, mod, s, e, t, v in self.db.execute(sql, args):
            vec = json.loads(v)
            scored.append({"id": cid, "modality": mod, "start": s, "end": e,
                           "text": t, "score": cosine(q, vec)})
        scored.sort(key=lambda r: -r["score"])
        return scored[:k]


def fuse_on_timeline(text_hits: list[dict], vis_hits: list[dict],
                     bucket_sec: float = 5.0, w_text: float = 0.6,
                     w_vis: float = 0.4) -> list[dict]:
    """Bucket both sides into 5s slots; weighted max per bucket with why-breakdown."""
    buckets: dict[tuple[str, int], dict] = {}
    for h in text_hits:
        key = (h.get("video_id", "v0"), int(h["start"] // bucket_sec))
        b = buckets.setdefault(key, {"t": key[1] * bucket_sec, "text": 0.0, "visual": 0.0})
        b["text"] = max(b["text"], h["score"])
    for h in vis_hits:
        key = (h.get("video_id", "v0"), int(h["start"] // bucket_sec))
        b = buckets.setdefault(key, {"t": key[1] * bucket_sec, "text": 0.0, "visual": 0.0})
        b["visual"] = max(b["visual"], h["score"])
    out = [{"t": b["t"], "score": w_text * b["text"] + w_vis * b["visual"],
            "why": {"text": round(b["text"], 3), "visual": round(b["visual"], 3)}}
           for b in buckets.values()]
    return sorted(out, key=lambda r: -r["score"])

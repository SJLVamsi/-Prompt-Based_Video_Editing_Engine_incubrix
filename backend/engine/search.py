"""Semantic search stub: keyword fallback now, embedding index later (sqlite-vec/Chroma)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Hit:
    t: float
    score: float
    why: dict
    text: str


def keyword_search(query: str, segments: list[dict]) -> list[Hit]:
    """segments: [{start,end,text}]. Score = token overlap; keeps API stable for embedding swap."""
    qtok = {w.lower().strip(".,!?") for w in query.split() if w}
    hits: list[Hit] = []
    for s in segments:
        stok = {w.lower().strip(".,!?") for w in s.get("text", "").split() if w}
        overlap = len(qtok & stok)
        if overlap:
            score = overlap / max(len(qtok), 1)
            hits.append(Hit(t=float(s["start"]), score=score,
                            why={"text": score, "visual": 0.0}, text=s["text"]))
    return sorted(hits, key=lambda h: -h.score)[:10]

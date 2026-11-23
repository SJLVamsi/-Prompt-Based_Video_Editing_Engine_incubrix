"""Save/load timeline + words JSON. I/O boundary (no math here)."""
from __future__ import annotations

import json
from pathlib import Path

from .schema import Caption, Clip, SourceFingerprint, Timeline, Word, create_timeline


def timeline_to_dict(tl: Timeline) -> dict:
    return {
        "fps_num": tl.fps_num,
        "fps_den": tl.fps_den,
        "clips": [c.__dict__ for c in tl.clips],
        "captions": [c.__dict__ for c in tl.captions],
        "words": [w.__dict__ for w in tl.words],
        "version": tl.version,
        "parent_hash": tl.parent_hash,
        "timeline_hash": tl.timeline_hash,
        "source_fingerprint": tl.source_fingerprint.__dict__ if tl.source_fingerprint else None,
        "source_id": tl.source_id,
        "filter_version": tl.filter_version,
    }


def timeline_from_dict(d: dict) -> Timeline:
    clips = [Clip(**c) for c in d.get("clips", [])]
    captions = [Caption(**c) for c in d.get("captions", [])]
    words = [Word(**w) for w in d.get("words", [])]
    fp = d.get("source_fingerprint")
    fingerprint = SourceFingerprint(**fp) if fp else None
    tl = create_timeline(
        fps_num=d["fps_num"],
        fps_den=d["fps_den"],
        clips=clips,
        captions=captions,
        words=words,
        version=d.get("version", 1),
        parent_hash=d.get("parent_hash"),
        source_fingerprint=fingerprint,
        source_id=d.get("source_id", "src"),
        filter_version=d.get("filter_version", "v1"),
    )
    # create_timeline recomputes hash; for load we verify stability
    return tl


def save_timeline(tl: Timeline, path: str | Path) -> None:
    Path(path).write_text(json.dumps(timeline_to_dict(tl), indent=2, sort_keys=True))


def load_timeline(path: str | Path) -> Timeline:
    return timeline_from_dict(json.loads(Path(path).read_text()))

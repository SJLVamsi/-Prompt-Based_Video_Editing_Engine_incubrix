"""Frozen timeline schema. All boundaries are frame ints + rational fps. No floats."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Word:
    id: str
    text: str
    start_frame: int
    end_frame: int
    conf: float = 1.0
    speaker: str | None = None

    def __post_init__(self) -> None:
        if self.start_frame < 0 or self.end_frame < 0:
            raise ValueError("word frames must be >= 0")
        if self.end_frame <= self.start_frame:
            raise ValueError(f"word {self.id} end must be > start")


@dataclass(frozen=True)
class Clip:
    id: str
    source_id: str
    start_frame: int
    end_frame: int
    speed_num: int = 1
    speed_den: int = 1
    anchor_start_word_id: str | None = None
    anchor_end_word_id: str | None = None

    def __post_init__(self) -> None:
        if self.start_frame < 0 or self.end_frame < 0:
            raise ValueError("clip frames must be >= 0")
        if self.end_frame <= self.start_frame:
            raise ValueError(f"clip {self.id} end must be > start")
        if self.speed_num <= 0 or self.speed_den <= 0:
            raise ValueError(f"clip {self.id} speed must be positive")


@dataclass(frozen=True)
class Caption:
    id: str
    text: str
    start_frame: int
    end_frame: int
    style: str = "subtitle"
    anchor_start_word_id: str | None = None
    anchor_end_word_id: str | None = None

    def __post_init__(self) -> None:
        if self.end_frame <= self.start_frame:
            raise ValueError(f"caption {self.id} end must be > start")
        if not self.text.strip():
            raise ValueError(f"caption {self.id} text must be non-empty")


@dataclass(frozen=True)
class SourceFingerprint:
    sha256: str
    size: int
    r_frame_rate_num: int = 30
    r_frame_rate_den: int = 1
    time_base_num: int = 1
    time_base_den: int = 90000

    def __post_init__(self) -> None:
        if self.r_frame_rate_den == 0 or self.time_base_den == 0:
            raise ValueError("fps/timebase denominators must be non-zero")


@dataclass(frozen=True)
class Timeline:
    fps_num: int
    fps_den: int
    clips: tuple[Clip, ...]
    captions: tuple[Caption, ...] = ()
    words: tuple[Word, ...] = ()
    version: int = 1
    parent_hash: str | None = None
    timeline_hash: str = ""
    source_fingerprint: SourceFingerprint | None = None
    source_id: str = "src"
    filter_version: str = "v1"

    def __post_init__(self) -> None:
        if self.fps_den == 0:
            raise ValueError("fps_den must be non-zero")
        if self.fps_num <= 0:
            raise ValueError("fps_num must be positive")

    @property
    def duration_frames(self) -> int:
        total = 0
        for c in self.clips:
            span = c.end_frame - c.start_frame
            # speed-adjusted output frames, rounded
            total += (span * c.speed_den + c.speed_num // 2) // c.speed_num if c.speed_num else 0
        return total


def _canonical_payload(
    fps_num: int,
    fps_den: int,
    clips: tuple[Clip, ...],
    captions: tuple[Caption, ...],
    words: tuple[Word, ...],
    version: int,
    parent_hash: str | None,
    source_fingerprint: SourceFingerprint | None,
    source_id: str,
    filter_version: str,
) -> dict:
    return {
        "captions": [c.__dict__ for c in sorted(captions, key=lambda x: (x.start_frame, x.id))],
        "clips": [c.__dict__ for c in sorted(clips, key=lambda x: (x.start_frame, x.id))],
        "filter_version": filter_version,
        "fps_den": fps_den,
        "fps_num": fps_num,
        "parent_hash": parent_hash,
        "source_fingerprint": source_fingerprint.__dict__ if source_fingerprint else None,
        "source_id": source_id,
        "version": version,
        "words": [w.__dict__ for w in sorted(words, key=lambda x: (x.start_frame, x.id))],
    }


def create_timeline(
    fps_num: int,
    fps_den: int,
    clips: list[Clip] | tuple[Clip, ...],
    captions: list[Caption] | tuple[Caption, ...] = (),
    words: list[Word] | tuple[Word, ...] = (),
    version: int = 1,
    parent_hash: str | None = None,
    source_fingerprint: SourceFingerprint | None = None,
    source_id: str = "src",
    filter_version: str = "v1",
) -> Timeline:
    """Factory that computes timeline_hash deterministically."""
    from .hash import compute_timeline_hash

    clips_t = tuple(clips)
    captions_t = tuple(captions)
    words_t = tuple(words)
    payload = _canonical_payload(
        fps_num, fps_den, clips_t, captions_t, words_t,
        version, parent_hash, source_fingerprint, source_id, filter_version,
    )
    h = compute_timeline_hash(payload)
    return Timeline(
        fps_num=fps_num,
        fps_den=fps_den,
        clips=clips_t,
        captions=captions_t,
        words=words_t,
        version=version,
        parent_hash=parent_hash,
        timeline_hash=h,
        source_fingerprint=source_fingerprint,
        source_id=source_id,
        filter_version=filter_version,
    )


def evolve_timeline(
    tl: Timeline,
    clips: tuple[Clip, ...] | None = None,
    captions: tuple[Caption, ...] | None = None,
    words: tuple[Word, ...] | None = None,
) -> Timeline:
    """Return new Timeline with bumped version + parent hash chain."""
    return create_timeline(
        fps_num=tl.fps_num,
        fps_den=tl.fps_den,
        clips=clips if clips is not None else tl.clips,
        captions=captions if captions is not None else tl.captions,
        words=words if words is not None else tl.words,
        version=tl.version + 1,
        parent_hash=tl.timeline_hash,
        source_fingerprint=tl.source_fingerprint,
        source_id=tl.source_id,
        filter_version=tl.filter_version,
    )

"""Undo/redo/restore as pointer moves + hash snapshots. No frame math here."""
from __future__ import annotations

from dataclasses import dataclass, field

from .errors import TimelineValidationError
from .schema import Timeline


@dataclass
class History:
    past: tuple[Timeline, ...] = ()
    present: Timeline | None = None
    future: tuple[Timeline, ...] = ()
    snapshots: dict[str, Timeline] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.present is not None:
            object.__setattr__(self, "snapshots", {**self.snapshots, self.present.timeline_hash: self.present})


def init_history(tl: Timeline) -> History:
    return History(past=(), present=tl, future=(), snapshots={tl.timeline_hash: tl})


def _with_snapshot(h: History, tl: Timeline) -> History:
    snaps = {**h.snapshots, tl.timeline_hash: tl}
    return History(past=h.past, present=h.present, future=h.future, snapshots=snaps)


def push(h: History, tl: Timeline) -> History:
    """Apply new timeline: present -> past, clear future (fork)."""
    assert h.present is not None
    snaps = {**h.snapshots, tl.timeline_hash: tl}
    return History(past=(*h.past, h.present), present=tl, future=(), snapshots=snaps)


def undo(h: History) -> tuple[History, bool]:
    """Return (new_history, did_nothing)."""
    if not h.past or h.present is None:
        return h, True
    new_future = (*h.future, h.present) if h.present else h.future
    new_present = h.past[-1]
    return History(past=h.past[:-1], present=new_present, future=new_future, snapshots=h.snapshots), False


def redo(h: History) -> tuple[History, bool]:
    if not h.future or h.present is None:
        return h, True
    new_past = (*h.past, h.present)
    new_present = h.future[-1]
    return History(past=new_past, present=new_present, future=h.future[:-1], snapshots=h.snapshots), False


def restore(h: History, target_hash: str) -> History:
    """Jump to snapshot; undoable (current present pushed to past, future cleared)."""
    if h.present is None:
        raise TimelineValidationError("EMPTY_HISTORY", "no present timeline")
    target = h.snapshots.get(target_hash)
    if target is None:
        # also allow prefix match
        matches = [t for hh, t in h.snapshots.items() if hh.startswith(target_hash)]
        if len(matches) == 1:
            target = matches[0]
        else:
            raise TimelineValidationError("NOT_FOUND", f"unknown snapshot hash: {target_hash}")
    if target.timeline_hash == h.present.timeline_hash:
        return h
    return History(past=(*h.past, h.present), present=target, future=(), snapshots=h.snapshots)

"""Mutation must fail on frozen dataclasses."""
import dataclasses

import pytest

from backend.engine.schema import Clip, create_timeline


def test_schema_frozen():
    tl = create_timeline(30, 1, [Clip("c1", "src", 0, 90)])
    with pytest.raises(dataclasses.FrozenInstanceError):
        tl.version = 99  # type: ignore[misc]
    c = tl.clips[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.start_frame = 5  # type: ignore[misc]

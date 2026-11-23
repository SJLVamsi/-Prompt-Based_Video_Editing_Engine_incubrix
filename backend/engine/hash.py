"""Deterministic hashing: canonical JSON + sha256."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def compute_timeline_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()[:16]


def replay_hash(source_sha256: str, plan_canonical: str, engine_version: str) -> str:
    msg = f"{source_sha256}|{plan_canonical}|{engine_version}".encode()
    return hashlib.sha256(msg).hexdigest()

"""Session runner: validated plans -> results.json + ops_log + replay hash. 3-way answers."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .errors import TimelineValidationError
from .hash import replay_hash
from .ops.caption import op_caption_add
from .ops.cut import op_cut
from .ops.keep import op_keep
from .ops.speed import op_speed
from .schema import Timeline, evolve_timeline
from .words import resolve_word_ids

ENGINE_VERSION = "engine-0.2.0+ffmpeg7"
ALLOWED_OPS = {"cut", "keep", "speed", "caption"}
ALLOWED_STYLES = {"hook", "subtitle", "cta"}


def parse_plan(raw: str) -> dict:
    """Strip fences, parse JSON, validate schema manually (no pydantic dep)."""
    s = raw.strip()
    if s.startswith("```"):
        # strip code fences
        lines = s.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        s = "\n".join(lines)
    start, end = s.find("{"), s.rfind("}")
    payload_s = s[start:end + 1] if start >= 0 and end > start else s
    try:
        plan = json.loads(payload_s)
    except json.JSONDecodeError as e:
        raise TimelineValidationError("INVALID_PLAN_JSON", f"plan is not JSON: {e}") from e
    return validate_plan(plan)


def validate_plan(plan: dict) -> dict:
    if not isinstance(plan, dict):
        raise TimelineValidationError("INVALID_PLAN", "plan must be an object")
    extra = set(plan) - {"version", "intent", "ops", "response", "clarify_question", "rejection_reason"}
    if extra:
        raise TimelineValidationError("INVALID_PLAN", f"extra keys forbidden: {sorted(extra)}")
    if plan.get("version") not in ("v1", 1, None) and plan.get("version") != "v1":
        # allow missing -> default; strict v1 otherwise
        if plan.get("version") != "v1":
            raise TimelineValidationError("INVALID_PLAN", "version must be 'v1'")
    ops = plan.get("ops", [])
    if not isinstance(ops, list) or not (1 <= len(ops) <= 50):
        # clarify/reject may carry empty ops
        if plan.get("response") in ("clarify", "reject"):
            ops = []
        else:
            raise TimelineValidationError("INVALID_PLAN", "ops must be list of 1..50")
    for op in ops:
        _validate_op(op)
    plan = {**plan, "ops": ops}
    plan.setdefault("response", "results")
    if plan["response"] not in ("results", "clarify", "reject"):
        raise TimelineValidationError("INVALID_PLAN", "response must be results|clarify|reject")
    return plan


def _validate_op(op: dict) -> None:
    if not isinstance(op, dict) or "op" not in op:
        raise TimelineValidationError("INVALID_OP", f"op must be object with 'op': {op}")
    if op["op"] not in ALLOWED_OPS:
        raise TimelineValidationError("INVALID_OP", f"unknown op: {op['op']}")
    for k in ("start", "end"):
        if k in op and not isinstance(op[k], (int, float)):
            raise TimelineValidationError("INVALID_OP", f"{op['op']}.{k} must be number")
    if "start" in op and "end" in op and not (op["end"] > op["start"]):
        raise TimelineValidationError("INVALID_OP", f"{op['op']} end must be > start")
    if op["op"] == "speed":
        f = float(op.get("factor", 1))
        if not (0.25 <= f <= 4.0):
            raise TimelineValidationError("BAD_SPEED", f"speed factor {f} outside 0.25-4")
    if op["op"] == "caption":
        t = str(op.get("text", ""))
        if not t.strip():
            raise TimelineValidationError("EMPTY_CAPTION", "caption text empty")
        if len(t) > 240:
            raise TimelineValidationError("BAD_CAPTION", "caption too long")
        if op.get("style", "subtitle") not in ALLOWED_STYLES:
            raise TimelineValidationError("INVALID_OP", "bad caption style")


def semantic_check(plan: dict, duration_sec: float) -> None:
    for op in plan.get("ops", []):
        for k in ("start", "end"):
            if k in op and not (0 <= float(op[k]) <= duration_sec + 1e-6):
                raise TimelineValidationError("OUT_OF_BOUNDS", f"{op['op']}.{k} outside duration")
        for v in (op.get("text", ""), op.get("reason", ""), op.get("label", "")):
            if "{" in str(v) and "}" in str(v) and "placeholder" in str(v).lower():
                raise TimelineValidationError("PLACEHOLDER", "plan contains placeholder")


class MockLLM:
    name = "mock"

    def __init__(self, script: dict[str, str]) -> None:
        self.script = script

    def complete(self, messages: list[dict], json_schema: dict | None = None) -> str:
        user = messages[-1].get("content", "") if messages else ""
        for k, v in self.script.items():
            if k in user:
                return v
        return '{"version":"v1","intent":"trim","response":"clarify","clarify_question":"What target duration?","ops":[]}'


def translate(prompt: str, ctx: str, llm, duration_sec: float, max_retries: int = 1) -> dict:
    system = "Emit JSON only with keys version,intent,ops,response. No extra keys."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt + "\n" + ctx}]
    raw = llm.complete(messages)
    for _ in range(max_retries + 1):
        try:
            plan = parse_plan(raw)
            semantic_check(plan, duration_sec)
            return plan
        except TimelineValidationError as e:
            messages = messages + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"Fix validation errors and re-emit JSON only: {e.code} {e.message}"},
            ]
            raw = llm.complete(messages)
    # deterministic fallback: clarify
    return {"version": "v1", "intent": "custom", "ops": [], "response": "clarify",
            "clarify_question": "Could you specify target duration and what to keep?"}


def apply_plan_to_timeline(tl: Timeline, plan: dict) -> Timeline:
    """Execute validated ops (seconds -> frames). Supports word ids via start_id/end_id."""
    from .timebase import t_to_frame
    from fractions import Fraction
    cur = tl
    word_ids = [w.id for w in tl.words]
    for op in plan.get("ops", []):
        kind = op["op"]
        if "start_id" in op or "end_id" in op:
            ids = []
            if "start_id" in op:
                ids.append(op["start_id"])
            if "end_id" in op and op["end_id"] != op.get("start_id"):
                # span from start_id to end_id inclusive by word order
                si = word_ids.index(op["start_id"]) if op["start_id"] in word_ids else None
                ei = word_ids.index(op["end_id"]) if op["end_id"] in word_ids else None
                if si is None or ei is None:
                    raise TimelineValidationError("DANGLING_WORD_ID", "unknown word id in op")
                lo, hi = (si, ei) if si <= ei else (ei, si)
                ids = word_ids[lo:hi + 1]
            s, e = resolve_word_ids(tl.words, ids)
        else:
            s = t_to_frame(Fraction(str(op["start"])), tl.fps_num, tl.fps_den)
            e = t_to_frame(Fraction(str(op["end"])), tl.fps_num, tl.fps_den)
        if kind == "cut":
            cur = op_cut(cur, [(s, e)])
        elif kind == "keep":
            cur = op_keep(cur, [(s, e)])
        elif kind == "speed":
            cur = op_speed(cur, s, e, *_factor_to_num_den(float(op.get("factor", 1))))
        elif kind == "caption":
            cur = op_caption_add(cur, str(op.get("text", "")), s, e, str(op.get("style", "subtitle")))
    return cur


def _factor_to_num_den(f: float) -> tuple[int, int]:
    from fractions import Fraction
    fr = Fraction(f).limit_denominator(100)
    return fr.numerator, fr.denominator


def run_session(
    session_dir: str | Path,
    prompt: str,
    timeline: Timeline,
    llm,
    source_sha256: str = "fixture",
) -> dict:
    """Run one turn; write results.json + ops_log.jsonl; return summary dict."""
    from .timebase import frame_to_t
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    duration_sec = float(frame_to_t(max((c.end_frame for c in timeline.clips), default=0),
                                    timeline.fps_num, timeline.fps_den))
    plan = translate(prompt, f"duration={duration_sec}", llm, duration_sec)
    if plan.get("response") != "results":
        result = {"status": plan["response"],
                  "question": plan.get("clarify_question", ""),
                  "reason": plan.get("rejection_reason", ""),
                  "plan": plan}
        (session_dir / "results.json").write_text(json.dumps(result, indent=2))
        with open(session_dir / "ops_log.jsonl", "a") as f:
            f.write(json.dumps({"prompt": prompt, "plan": plan}) + "\n")
        return result
    out_tl = apply_plan_to_timeline(timeline, plan)
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"))
    rh = replay_hash(source_sha256, canonical, ENGINE_VERSION)
    result = {"status": "done", "plan": plan, "replay_hash": rh,
              "timeline_hash": out_tl.timeline_hash,
              "outputs": {"timeline_frames": out_tl.duration_frames}}
    (session_dir / "results.json").write_text(json.dumps(result, indent=2))
    with open(session_dir / "ops_log.jsonl", "a") as f:
        f.write(json.dumps({"prompt": prompt, "plan": plan, "replay_hash": rh,
                            "timeline_hash": out_tl.timeline_hash}) + "\n")
    (session_dir / "replay.hash").write_text(rh)
    return result

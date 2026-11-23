"""Minimal FastAPI: healthz/readyz/manifest + jobs with idempotency + SSE (in-memory MVP)."""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

FFMPEG_VERSION = "7.x"
API_VERSION = "v1"


class Problem(BaseModel):
    type: str
    title: str
    status: int
    code: str
    detail: str = ""
    traceId: str = ""
    retryable: bool = False


def problem(code: str, detail: str, status: int = 400, retryable: bool = False) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"type": f"https://api.local/problems/{code.lower()}", "title": code,
                 "status": status, "code": code, "detail": detail,
                 "traceId": uuid.uuid4().hex[:8], "retryable": retryable},
    )


JOBS: dict[str, dict[str, Any]] = {}
IDEM: dict[str, str] = {}  # idempotency-key+body-hash -> jobId


def create_app() -> FastAPI:
    app = FastAPI(title="Prompt-Based Video Editing Engine")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/readyz")
    def readyz():
        return {"ok": True, "checks": {"ffmpeg": FFMPEG_VERSION, "store": "memory"}}

    @app.get("/manifest")
    def manifest():
        return {"apiVersion": API_VERSION, "ffmpeg": FFMPEG_VERSION,
                "features": {"wordTimestamps": True, "sse": True},
                "limits": {"maxDurationMin": 60}, "presets": ["preview", "720p", "1080p", "short"]}

    @app.get("/version")
    def version():
        return {"version": "0.2.0"}

    @app.post("/v1/plans:generate")
    def plan_generate(body: dict):
        from backend.engine.session import parse_plan
        try:
            plan = parse_plan(body.get("raw", "{}"))
            return {"plan": plan, "warnings": []}
        except Exception as e:
            return problem("E_VALIDATION", str(e), 422)

    @app.post("/v1/renders")
    def renders(body: dict, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
        plan = body.get("plan", {})
        asset = body.get("assetId", "demo")
        key = f"{idempotency_key}:{hash(str(sorted(plan.items())) if isinstance(plan, dict) else plan)}"
        if idempotency_key and key in IDEM:
            jid = IDEM[key]
            return JSONResponse({"jobId": jid, "replayed": True})
        jid = uuid.uuid4().hex[:8]
        JOBS[jid] = {"jobId": jid, "state": "queued", "type": "render",
                     "progress": 0.0, "assetId": asset, "plan": plan,
                     "created_at": time.time()}
        if idempotency_key:
            IDEM[key] = jid
        return {"jobId": jid}

    @app.get("/v1/jobs/{job_id}")
    def job_get(job_id: str):
        if job_id not in JOBS:
            return problem("E_NOT_FOUND", "job not found", 404)
        return JOBS[job_id]

    @app.post("/v1/jobs/{job_id}/cancel")
    def job_cancel(job_id: str):
        if job_id not in JOBS:
            return problem("E_NOT_FOUND", "job not found", 404)
        JOBS[job_id]["state"] = "canceled"
        return JOBS[job_id]

    @app.get("/v1/jobs/{job_id}/events")
    def job_events(job_id: str):
        def gen():
            yield 'data: {"progress": 1.0}\n\n'
        return StreamingResponse(gen(), media_type="text/event-stream")

    return app


app = create_app()

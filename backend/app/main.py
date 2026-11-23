"""Minimal FastAPI: healthz/readyz/manifest + jobs with idempotency + SSE (in-memory MVP).

UAT slice (real media, sync for determinism): /v1/uploads, /v1/transcribe,
/v1/uat/run (silence + subtitles + 9:16), /v1/exports/{job}/download.
Uploads/renders live in $UPLOAD_TMP (ephemeral — demo scope).
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Header, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
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
ASSETS: dict[str, dict[str, Any]] = {}  # assetId -> {path, duration, fps_num, fps_den, width, height, words}

UPLOAD_DIR = Path(os.environ.get("UPLOAD_TMP", "/tmp/uploads"))
RENDER_DIR = Path(os.environ.get("RENDER_TMP", "/tmp/renders"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".mp4", ".mov", ".m4v", ".wav", ".mp3"}
MAX_UPLOAD_MB = 100


def _eng():
    """Layout-agnostic engine imports (container /code vs repo root)."""
    try:
        from engine.words import ingest_transcript
        from engine.schema import Clip, create_timeline
        from engine.ops.cut import op_cut
        from engine.silence import word_gap_cuts
        from engine.cues import cues_to_srt, words_to_cues
        from engine.render.graph import build_graph
        from engine.render.ffmpeg import build_ffmpeg_cmd, run_cmd
        from engine.render.probe import probe as _probe
        from engine.render.ffmpeg import require_text_burnin
        from engine.timebase import parse_r_frame_rate
        from engine.transcribe import transcribe_file
    except ImportError:
        from backend.engine.words import ingest_transcript
        from backend.engine.schema import Clip, create_timeline
        from backend.engine.ops.cut import op_cut
        from backend.engine.silence import word_gap_cuts
        from backend.engine.cues import cues_to_srt, words_to_cues
        from backend.engine.render.graph import build_graph
        from backend.engine.render.ffmpeg import build_ffmpeg_cmd, run_cmd
        from backend.engine.render.probe import probe as _probe
        from backend.engine.render.ffmpeg import require_text_burnin
        from backend.engine.timebase import parse_r_frame_rate
        from backend.engine.transcribe import transcribe_file
    return (ingest_transcript, Clip, create_timeline, op_cut, word_gap_cuts,
            cues_to_srt, words_to_cues, build_graph, build_ffmpeg_cmd,
            run_cmd, _probe, require_text_burnin, parse_r_frame_rate,
            transcribe_file)


def _probe_asset(path: str) -> dict:
    import json, subprocess
    p = subprocess.run(["ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-show_entries", "stream=codec_type,r_frame_rate,width,height",
                        "-of", "json", path],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {p.stderr[-500:]}")
    info = json.loads(p.stdout)
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    return {"duration": float(info.get("format", {}).get("duration", 0.0)),
            "r_frame_rate": v.get("r_frame_rate", "30/1"),
            "width": int(v.get("width", 0) or 0),
            "height": int(v.get("height", 0) or 0)}


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
        try:  # container layout (/code -> engine.*)
            from engine.session import parse_plan
        except ImportError:  # repo layout (root -> backend.engine.*)
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

    @app.post("/v1/uploads")
    def uploads(file: UploadFile = File(...)):
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXT:
            return problem("E_VALIDATION", f"extension {ext!r} not allowed {sorted(ALLOWED_EXT)}", 415)
        aid = uuid.uuid4().hex[:8]
        dest = UPLOAD_DIR / f"{aid}{ext}"
        size = 0
        with open(dest, "wb") as f:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_MB * 1024 * 1024:
                    dest.unlink(missing_ok=True)
                    return problem("E_VALIDATION", f"file exceeds {MAX_UPLOAD_MB}MB", 413)
                f.write(chunk)
        try:
            meta = _probe_asset(str(dest))
        except RuntimeError as e:
            dest.unlink(missing_ok=True)
            return problem("E_PROBE_FAILED", str(e), 422)
        if meta["duration"] <= 0:
            dest.unlink(missing_ok=True)
            return problem("E_PROBE_FAILED", "zero-duration media", 422)
        ASSETS[aid] = {"path": str(dest), "duration": meta["duration"],
                       "r_frame_rate": meta["r_frame_rate"],
                       "width": meta["width"], "height": meta["height"],
                       "words": None}
        return {"assetId": aid, **ASSETS[aid], "path": None}

    @app.post("/v1/transcribe")
    def transcribe(body: dict):
        aid = body.get("assetId", "")
        if aid not in ASSETS:
            return problem("E_NOT_FOUND", "asset not found; upload first", 404)
        model = body.get("model", "tiny")
        (_, _, _, _, _, _, _, _, _, _, _, _, _, transcribe_file) = _eng()
        try:
            res = transcribe_file(ASSETS[aid]["path"], model=model)
        except RuntimeError as e:
            return problem("E_TRANSCRIBE_UNAVAILABLE", str(e), 503, retryable=True)
        words = [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in res.words]
        ASSETS[aid]["words"] = words
        return {"assetId": aid, "words": words, "n": len(words), "model": model}

    @app.post("/v1/uat/run")
    def uat_run(body: dict):
        """Deterministic rule-based execution of the UAT prompt class.

        Intents detected by keyword (documented, testable — not faux-AI):
        silence ("silence|silent|quiet"), subtitles ("subtitle|caption"),
        vertical ("9:16|vertical|short|reel"). Unknown -> clarify, no render.
        """
        (ingest_transcript, Clip, create_timeline, op_cut, word_gap_cuts,
         cues_to_srt, words_to_cues, build_graph, build_ffmpeg_cmd,
         run_cmd, _probe, require_text_burnin, parse_r_frame_rate,
         _transcribe) = _eng()
        aid = body.get("assetId", "")
        prompt = str(body.get("prompt", ""))
        if aid not in ASSETS:
            return problem("E_NOT_FOUND", "asset not found; upload first", 404)
        a = ASSETS[aid]
        if not a.get("words"):
            return problem("E_TRANSCRIBE_MISSING", "transcribe the asset first", 422)
        pl = prompt.lower()
        want_silence = any(k in pl for k in ("silence", "silent", "quiet"))
        want_subs = any(k in pl for k in ("subtitle", "caption"))
        want_vert = any(k in pl for k in ("9:16", "vertical", "short", "reel"))
        if not (want_silence or want_subs or want_vert):
            return {"status": "clarify",
                    "clarify_question": "Which edit? I can: remove silence, add subtitles, convert to 9:16.",
                    "ops": []}
        fps_num, fps_den = parse_r_frame_rate(a["r_frame_rate"])
        words = ingest_transcript({"words": a["words"]}, fps_num, fps_den)
        dur_f = max(w.end_frame for w in words)
        tl = create_timeline(fps_num, fps_den, [Clip("c1", "src", 0, dur_f)], words=words)
        ops: list[str] = []
        if want_silence:
            cuts = word_gap_cuts(words, fps_num, fps_den)
            if cuts:
                tl = op_cut(tl, cuts)
            ops.append(f"cut-silence:{len(cuts)}")
        cues = words_to_cues(words, fps_num, fps_den) if want_subs else ()
        srt_path = None
        if want_subs:
            srt_path = RENDER_DIR / f"{aid}.srt"
            srt_path.write_text(cues_to_srt(cues, fps_num, fps_den))
            ops.append(f"subtitles:{len(cues)}-cues")
        vf_tail = ""
        if want_vert:
            w, h = a["width"] or 640, a["height"] or 480
            want_w = min(w, int(h * 9 / 16))
            x = (w - want_w) // 2
            vf_tail = f"crop={want_w}:{h}:{x}:0,scale=1080:1920,setsar=1"
            ops.append("vertical:1080x1920")
        g = build_graph(tl, vf_video_tail=vf_tail)
        fps_s = f"{fps_num}/{fps_den}" if fps_den != 1 else f"{fps_num}"
        tmp_out = RENDER_DIR / f"{aid}_cut.mp4"
        cmd = build_ffmpeg_cmd(g, preset="preview", fps=fps_s,
                               input_path=a["path"], output_path=str(tmp_out))
        rc, err = run_cmd(cmd)
        if rc != 0:
            return problem("E_RENDER_FFMPEG", err[-1000:], 500, retryable=True)
        final = tmp_out
        sub_stream = False
        warnings: list[str] = []
        if srt_path is not None:
            import subprocess
            soft = RENDER_DIR / f"{aid}_final.mp4"
            # Deterministic delivery on every build: sidecar SRT + mov_text
            # soft-sub mux. (Burned-in `subtitles=` needs libass, absent from
            # the Homebrew dev build; the Debian image has it, but soft-sub
            # keeps output identical everywhere. See require_text_burnin.)
            r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp_out),
                                "-i", str(srt_path), "-c", "copy", "-c:s", "mov_text",
                                str(soft)], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                return problem("E_RENDER_FFMPEG", r.stderr[-500:], 500, retryable=True)
            final = soft
            sub_stream = True
        if want_silence and not any(o.startswith("cut-silence:") and not o.endswith(":0") for o in ops):
            warnings.append("no silence gaps >=0.5s found; nothing cut")
        jid = uuid.uuid4().hex[:8]
        JOBS[jid] = {"jobId": jid, "state": "succeeded", "type": "uat-render",
                     "progress": 1.0, "assetId": aid, "result": str(final),
                     "srt": str(srt_path) if srt_path else None,
                     "sub_stream": sub_stream}
        meta = _probe_asset(str(final))
        return {"status": "done", "jobId": jid, "ops": ops,
                "duration": meta["duration"], "width": meta["width"],
                "height": meta["height"], "sub_stream": sub_stream,
                "warnings": warnings}

    @app.get("/v1/exports/{job_id}/download")
    def export_download(job_id: str):
        if job_id not in JOBS or "result" not in JOBS[job_id]:
            return problem("E_NOT_FOUND", "result not found", 404)
        return FileResponse(JOBS[job_id]["result"], media_type="video/mp4",
                            filename=f"{job_id}.mp4")

    return app


app = create_app()

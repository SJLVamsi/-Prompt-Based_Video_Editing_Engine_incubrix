# BLOCKERS — Unresolved Issues

> One row per blocker: date, severity (P0/P1/P2), issue, impact, workaround/owner, resolution.
> Honest failures belong here + in test pack (brief scores this).

| Date | Sev | Issue | Impact | Workaround / Owner | Status |
|---|---|---|---|---|---|
| 2026-11-23 | P1 | Remote repo was empty; no upstream work to preserve | None — clean start, but confirms no hidden spec | Owner: setup agent — initialized `main` locally, will push planning commit | Open until first push verified |
| 2026-11-23 | P1 | Vendor limits are snapshots (Groq/Gemini/Render/HF change frequently) | Quota/math may be stale at build time | Re-check `console.groq.com/docs/rate-limits`, `aistudio.google.com/docs/pricing` + rate-limit page, `render.com/docs/free`, `huggingface.co/docs/hub/spaces-overview` at Phase 4/6 start; record date + account numbers here | Open |
| 2026-11-23 | P1 | HF gated weights need per-account acceptance + token (`pyannote/segmentation-3.0` + `speaker-diarization-3.1`) | CI/reviewers cannot pull without tokened account | Keep diarization optional; container reads `HF_TOKEN` env; never ask reviewers to supply; offline cache after first pull | Open (by design) |
| 2026-11-23 | P2 | Free-tier LLM trains on content (Gemini free = Yes) | Confidential brief/test videos must not go to free tier | `MockLLM` default; real adapters slow/manual + `--allow-free-tier` gate + redaction | Open (by design) |
| 2026-11-23 | P2 | HF Spaces single container/port; Compose will not run there | Demo hosting choice constrained | DECIDED 2026-11-23: demo = Docker Compose local + tunnel (user choice). Render free only as backup with external MinIO + cold-start warning | Decided — implement in Phase 6.3 |

## Resolved
- (none yet)

## New (2026-11-23 build)
- RESOLVED 2026-11-23: `ffmpeg` installed via brew (9.0.2). Slow lane green. Note: FFmpeg 9 removed `-vsync`; codebase now uses `-fps_mode cfr/vfr`.
- faster-whisper weights not installed (by design, slow lane) — `transcribe.py` raises clean RuntimeError; fixture path covers fast lane.

# AGENTS.md — Permanent Engineering Rules
### Prompt-Based Video Editing Engine (`-Prompt-Based_Video_Editing_Engine_incubrix`)

> Source of truth for every agent and human contributor. Read this before any task.
> Stack: Next.js, React, TypeScript, FastAPI, Python, FFmpeg, OpenCV, pretrained AI models.

## 0. Session & Planning System

- Planning docs live in `docs/`:
  - `docs/MASTER_GOAL.md` — full spec
  - `docs/ARCHITECTURE.md` — technical architecture
  - `docs/RESEARCH_PLAN.md` — research topics
  - `docs/FEATURES.md` — feature breakdown
  - `docs/ROADMAP.md` — phased executable plan
  - `docs/progress/MASTER_CHECKLIST.md` — all tasks + status
  - `docs/progress/CURRENT_STATUS.md` — where we are
  - `docs/progress/SESSION_HANDOFF.md` — how to resume
  - `docs/progress/BLOCKERS.md` — unresolved issues
  - `docs/progress/GIT_LOG.md` — verified commit/push history
- Update the relevant `docs/progress/*` file(s) in the **same commit** as any code change.
- Small, independently testable tasks only. Each task: test → implement → verify → commit → push.
- Never commit: secrets (`.env`, tokens), caches, `__pycache__/`, `node_modules/`, large media (`*.mp4`, `*.wav` >5MB unless fixture), model weights (`*.pt`, `*.bin`, `*.onnx`).

## 1. Five Non-Negotiables (from brief analysis)

1. **1-frame sync, no clipped words.** Timing is the #1 risk: sync drift after cuts, VFR phone video, word timestamps slightly off.
2. **Frame numbers / exact fractions + word-ID anchors.** Store every boundary as frame `int` or `Fraction`, attach edits to word IDs. Float seconds and rounded cut times accumulate drift across many cuts.
3. **Single FFmpeg filter-graph re-encode from original.** Stream copy (`-c copy`) cannot cut where asked (keyframes only). Always re-encode via one `-filter_complex`.
4. **LLM is translator only.** Validate output against a schema (Pydantic/Zod). Failures → clarifying question or rejection. Store parsed ops with each step; replays must give same `timeline_hash`.
5. **Do not trust raw STT.** Whisper can hallucinate silence, word times can clip, speaker labels can be wrong. VAD filter + padding + confidence gating required.

## 2. Contracts First

- Backend canonical schemas: `backend/app/models/schemas.py` (Pydantic v2).
- Frontend mirrors: `frontend/lib/contracts.ts` (Zod). CI checks parity via `contracts/*.schema.json` fixtures.
- No feature without: exact file paths, function signatures, and a failing test checked in first.
- `Timeline` is immutable (`frozen`). Ops are pure functions `(Timeline, params) -> Timeline`, no I/O inside.

## 3. Time & Media Rules

- Internal time = `int` frames + `Fraction(fps_num, fps_den)`. Floats only at FFmpeg string emission.
- Canonical FPS stored as `fps_num/fps_den` (e.g. `24000/1001`, `30000/1001`, `30/1`). Never store `23.976` as float.
- `start_frame` inclusive, `end_frame` exclusive. Duration = `end - start`.
- Probe and fingerprint every source: `sha256 + size + r_frame_rate + time_base + duration + rotation`. Refuse render on mismatch.
- Phone/VFR: normalize to CFR at decode head (`fps=...:round=near`), `aresample=osr=48000:async=1`, emit `-vsync cfr`.
- Word padding: expand cuts by 80–120ms each side; never cut tighter than word boundary + padding.
- Audio: AAC 48kHz stereo, `+faststart`, `avoid_negative_ts make_zero`. Tolerance: duration ±1.5 frames, A/V offset <20ms.

## 4. FFmpeg Rules

- One `-filter_complex` graph per render: `trim=start_frame:end_frame + setpts` per segment → `concat` → `format/subtitles/scale` → single `libx264` + `aac` encode.
- Video trim uses `trim=start_frame:end_frame`; audio uses `atrim=start=<sec 6dp>:end=... + asetpts`. Always `setpts=PTS-STARTPTS` per segment before concat.
- Speed: video `setpts=(1/speed)*PTS`, audio `atempo` chain (0.5–2.0 per stage).
- Never rely on auto `-map`; always `-map "[vout]" -map "[aout]"`.
- Log always: full filter graph string + `timeline_hash` + `ffmpeg -version` + stderr on failure.

## 5. STT / Diarization Rules

- Engine must run from a saved transcript JSON fixture without any STT (decouples engine tests from models).
- Real STT: `faster-whisper` with VAD filter (`vad_filter=True`, tune `threshold/min_silence_duration_ms/speech_pad_ms`). `word_timestamps=True`.
- Treat silence hallucinations as expected: drop low-confidence words in detected silence.
- pyannote `speaker-diarization-3.1` (MIT, HF token required, accept conditions for pipeline + `segmentation-3.0`) is optional; never gate edits on speaker labels alone.
- Subtitles: group words into 1.5–6s cues, ≤42 chars/line, SRT/VTT + ASS burn-in via `subtitles=` filter.

## 6. LLM Adapter Rules

- System prompt constrains output to JSON ops only. Temperature ~0. Validate with Pydantic; one retry; then 3-way answer: `clarify | reject | results`.
- `results.json` per session step: `{prompt, parsed_ops, timeline_hash, warnings}`. Deterministic replay: same ops → same hash.
- Mock adapter for all tests (golden JSON). Real adapters (Groq `gpt-oss`, Gemini flash) only in `slow`/manual runs. Never paste confidential brief into free-tier endpoints that train on data.
- Store `planHash` on jobs; idempotency: same `Idempotency-Key` + same body → replay same `jobId`; same key + different body → `422 IDEMPOTENCY_MISMATCH`.

## 7. Jobs / API / Storage Rules

- Endpoints versioned `/v1`. Error model RFC 7807 `problem+json` with stable `code` (`E_VALIDATION`, `E_RENDER_FFMPEG`, …) + `traceId` + `retryable`.
- Jobs: `queued → running → succeeded|failed|canceled`, `retrying` max 3 with backoff. DB is truth; Redis pub/sub only for progress. SSE `GET /v1/jobs/{id}/events`.
- `GET /healthz` (no deps), `GET /readyz` (pg+redis+minio+ffmpeg), `GET /manifest` (versions, presets, limits).
- Storage via MinIO presigned URLs; backend never proxies bytes. Buckets: `raw-uploads`, `renders`, `thumbs`, `transcripts`.
- `docker compose up` must bring `api + worker + minio + postgres + redis + frontend` with no manual steps beyond `cp .env.example .env`.

## 8. Frontend Rules

- `Next.js` App Router + TypeScript strict + Tailwind. Timeline store via `zustand`; undo as Command pattern (not snapshots), cap 100, coalesce drags/typing.
- Frame-snapped interactions: `Math.round(t*fps)/fps`. Keyboard: `Space, J/K/L, ←/→ ±1 frame, Shift+←/→ ±1s, C split, Del cut, Cmd+Z/Y`.
- Word↔playhead bidirectional linking; click word → seek; playhead → highlight + autoscroll (throttled).
- No `any` without justification; `tsc --noEmit` + `eslint` clean on every commit.

## 9. Testing & Verification Rules

- TDD: failing test first, run to see red, minimal implement, run to see green, commit.
- Fast lane (every PR, no weights/network/encode): unit + contract parity + API with mocks. Slow lane (nightly/label): real `ffmpeg` + tiny Whisper + Playwright chromium.
- Golden 8-step fixture (`tests/test_golden_8step.py`) is the onboarding spec — keep green.
- Test pack must include honest failures (brief explicitly scores this). Record failed attempts in `docs/progress/*`, not hidden.
- Before claiming done: run the command, paste output, `ffprobe` durations, A/V offsets where relevant.

## 10. Hosting / Secrets / Licences

- Render free: ephemeral FS, SQLite lost on restart/redeploy, 15-min sleep + ~1-min wake. Keep state in MinIO/external. Check reviewer tolerance for cold start.
- HF Spaces: static free; Gradio/Docker need paid except 2 ZeroGPU Gradio for free personal accounts. Single container / single port — multi-container Compose will not run there. Re-check docs before depending on numbers.
- Groq STT (Developer plan, verify for your account): `whisper-large-v3/turbo` ~20 req/min, 2000/day, 7200 audio-s/hr, 28800/day (8h). LLM `gpt-oss/qwen` ~30 req/min, 1000/day, 8000 TPM.
- Gemini free tier: some flash/lite free; newer models free tier unavailable; free tier trains on content — confidential brief/test videos need care.
- `pyannote/speaker-diarization-3.1` + `segmentation-3.0`: MIT, HF token + accept conditions required; container needs secret; do not ask reviewers to supply it.
- `openai/whisper` + `SYSTRAN/faster-whisper` repos: MIT. Weights: see model cards. Limits change — re-read vendor page before depending on a number.

## 11. Git Workflow

- `main` only (or feature branch + PR if requested). After each verified unit: `git add <sources+tests+docs>`, `git commit -m "type: concise"`, `git push origin main`, append row to `docs/progress/GIT_LOG.md` with hash + `git status` clean proof.
- Commit types: `docs:`, `feat:`, `fix:`, `test:`, `chore:`.
- Before push: `git status --short`, no secrets/caches/media/weights (`git ls-files` spot check).

## 12. Definition of Done (per task)

- [ ] Failing test written & observed red
- [ ] Minimal implementation, test green
- [ ] `ruff + mypy` (backend) / `tsc + eslint` (frontend) clean where applicable
- [ ] Docs (`FEATURES/ROADMAP/MASTER_CHECKLIST/CURRENT_STATUS`) updated in same commit
- [ ] Committed + pushed, hash recorded in `GIT_LOG.md`

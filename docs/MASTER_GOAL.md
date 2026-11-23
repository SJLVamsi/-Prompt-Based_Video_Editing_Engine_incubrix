# MASTER_GOAL — Prompt-Based Video Editing Engine

**Repo:** https://github.com/SJLVamsi/-Prompt-Based_Video_Editing_Engine_incubrix
**Status:** Planning phase — no implementation yet. This doc is source of truth.
**Stack:** Next.js, React, TypeScript, FastAPI, Python, FFmpeg, OpenCV, pretrained AI (Whisper/faster-whisper, pyannote, CLIP/SigLIP, BGE, vision LLM, Groq/Gemini LLM)

## 1. Vision

A user uploads a video, types (or speaks) **"cut silences, keep the demo, make a 30s Short with captions"**, and gets back a frame-accurate, watchable edit plus a web timeline they can refine conversationally — with undo/redo/restore, semantic search, and one-click export.

## 2. Must-Haves (P0 — judged first)

1. **1-frame sync, no clipped words** after any number of cuts.
   - Measure: `|probe_duration − expected| < 1.5 frames`; `|video_start − audio_start| < 20ms`; no word cut tighter than boundary + 80–120ms pad.
2. **Frame/exact-fraction boundaries + word-ID content anchors.**
   - Every boundary = frame `int` + `fps_num/fps_den` (`Fraction`). Edits attach to `word_id`s, not float seconds.
3. **Original → single filter-graph re-encode.**
   - No `-c copy` cuts. One `-filter_complex` (`trim/start_frame` + `setpts` → `concat` → `format/subtitles/scale` → `libx264+aac`).
4. **LLM as translator only.**
   - JSON ops validated by Pydantic/Zod; failures → `clarify` question or `reject`; every step stores `{prompt, parsed_ops, timeline_hash}` in `results.json`; replay same ops → same hash.
5. **Distrusted STT pipeline.**
   - faster-whisper with VAD, padding, confidence gating; pyannote labels advisory only.

## 3. Core Features (P1)

- Core video editing: cut / keep / trim / split / speed (0.25–4×) as pure functions on immutable `Timeline`.
- Natural-language editing: prompt → `EditPlan{cut,keep,speed,caption}` (closed vocab).
- FFmpeg render service + `ffprobe` fingerprinting + CFR normalization (23.976 + VFR phone).
- Whisper transcription (`large-v3-turbo` default, `word_timestamps=True`, `vad_filter=True`).
- Silence removal: word-gap method primary (gap ≥0.4–0.8s → shorten to 0.3s + 200ms keep); `silenceremove`/`silencedetect` preview only.
- Subtitle generation: words → 1.5–6s cues, ≤42 chars/line, SRT/VTT sidecars + ASS burn-in.
- Semantic scene search: transcript embeddings (BGE) + frame CLIP embeddings, dual index (`sqlite-vec`/Chroma MVP), timeline-bucket fusion.
- Multimodal understanding: PySceneDetect → keyframes → CLIP embed + vision-LLM captions (top-K only).
- Intelligent planning + constraint-aware editing: duration knapsack, 9:16 face-aware crop, hook scorer, loudnorm −14 LUFS.
- Auto Shorts/Reels: hook + 2–4 beats + CTA, ≤60s (target 25–35s), 1080×1920, burned captions, 3 hook variants.
- Conversational editing: multi-turn `SessionState`, intent taxonomy (`refine|undo|redo|restore|clarify`), pointer-based undo (no LLM re-call).
- Undo/redo/restore: Command pattern (frontend) + `History{past,present,future}` + `ops_log.jsonl` replay hashes (backend).
- Web timeline: 3 tracks (V1/A1/C1), waveform canvas, playhead RAF, word-linked transcript, drag cut handles, keyboard map.
- Video export: presets (`preview/720p/1080p/short`), `+faststart`, AAC 48k stereo, thumbnail + storyboard, presigned MinIO download, SSE progress.

## 4. Product Surfaces

- `frontend/` (Next.js App Router): landing/new-project, `projects/[projectId]` editor shell (timeline + preview + transcript + prompt bar + jobs), caption editor, share/export.
- `backend/` (FastAPI `/v1`): `upload, transcribe, plan, edit/preview, render, jobs, export, system(healthz/readyz/manifest/version)`.
- `docker-compose.yml`: `api + worker(arq) + minio + postgres + redis + frontend`. `docker compose up` works after `cp .env.example .env`.
- `results.json` per session step + `ops_log.jsonl` + `edl.json` + `replay.hash` stored alongside render in MinIO.

## 5. Non-Functional Targets

- Fast lane (PR): <5 min, no weights/network/encode. Slow lane (nightly): tiny Whisper + ≤10s fixtures + 1×720p + Playwright chromium.
- Frontend: LCP <2s on Fast 3G for editor shell skeleton; initial JS <150KB gzipped for landing.
- API: p95 `plan:generate` <30s (sync) else job; presign <300ms; job poll <200ms.
- Render: 1-min 1080p → <2× realtime on 4vCPU reference worker (log `tookMs`).
- Confidentiality: never paste brief/PII into free-tier LLM that trains on data; gate with `--allow-free-tier` flag.

## 6. Evidence Required (per brief)

- Live demo (deployed or local Compose with public URL).
- ≥15 sessions in test pack with `results.json` (include honest failures).
- Test pack: golden 8-step + unit + contract parity + API + slow sync/VFR/23.976 + e2E.
- Submission Form + 8-minute video. Reserve last hours for this; failed attempts stay in pack.

## 7. Out of Scope for MVP

- OpenTimelineIO export, 60-min latency target, 40-scenario CI gate (count 10/100 marks only if every item in level verified — likely to drop first per brief).
- Multi-container hosting on HF Spaces (single container/port only); Render free as demo only (ephemeral FS).
- Real-time collaborative editing, paid APIs as hard deps, mobile native apps.

## 8. Acceptance Checklist (done = all true)

- [ ] Golden 8-step green (`testsrc`+`sine` synthetic, hash-stable replay).
- [ ] 23.976 clip + VFR phone clip measured (drift + A/V offset logged).
- [ ] ≥15 sessions `results.json` with 3-way answers represented (results/clarify/reject).
- [ ] Undo/redo/restore round-trip identical hash.
- [ ] `docker compose up` + smoke (`presign→upload→transcribe→plan→render→download`) green.
- [ ] Submission Form + 8-min video delivered.

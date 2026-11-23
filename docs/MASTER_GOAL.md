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

---

## 9. Appendix — Original Master Prompt (verbatim, preserved 2026-11-23)

> The text below is the original project brief supplied by the user on 2026-11-23, preserved word-for-word so no detail is lost. The synthesized spec in §§1–8 above derives from it; on any conflict, this appendix is the tie-breaker for intent.

```
my topic is Prompt-Based Video Editing Engine

Five things that matter most
1
Timing is a recurring theme in the discussions I read: sync drift after cuts, variable frame rate phone video, and word timestamps that are slightly off. I chose these threads by searching, so this is not a count of how common each problem is. Your must-haves (1-frame sync, no clipped words) sit right in that area, which is why I put it first.
2
Store every boundary as a frame number or exact fraction, and attach edits to word IDs. Float seconds and rounded cut times add up to drift across many cuts (problem 2).
3
Render from the original in one filter graph and re-encode. Stream copy cannot cut where you ask (problem 1).
4
Treat the language model as a translator only. Validate its output against a schema, turn failures into a question or a rejection, and keep the parsed operations with each step so replays give the same hash (problem 9).
5
Do not trust raw speech-to-text. Whisper can invent text in silence, word times can be off by enough to clip words, and speaker labels can be wrong (problems 6, 7, 8).
Suggested build order
This order is my own suggestion. It follows the brief's priority (must-haves, then Core) and leaves time for the evidence the brief asks for, which is easy to underestimate.
1
Timeline schema, edit history, content anchors (word IDs, frame numbers), timeline_hash, source file hash. Unit tests with no video and no AI.
2
Transcript: start with a saved transcript file as test input, so the engine does not wait on speech recognition. Then add real speech recognition with a voice activity filter.
3
Operations as plain functions on the timeline: cut, keep, speed, caption, undo, redo, restore. Test the 8-step worked example here, before any rendering.
4
Three-way answers and the session runner producing results.json.
5
Renderer: one ffmpeg filter graph from the timeline. Measure A/V offset and length difference after many edits on a 23.976 fps clip, and on a phone clip.
6
Language model adapter with schema validation, plus the mock adapter.
7
HTTP API, jobs, idempotency, errors, health, manifest, Docker Compose with MinIO and the batch runner.
8
Live demo, 15 or more sessions, test pack, Submission Form, 8-minute video. Reserve the last hours for this. Failed attempts belong in the test pack: the brief says honest failures score better than hidden ones.
Likely to drop first
Outstanding items such as OpenTimelineIO export, the 60-minute latency target and 40 CI scenarios. They count for 10 of 100 marks and only if every item in the level is verified.
Hosting, API access and licences
These are current vendor pages. Limits and prices change, so read the page again before you depend on a number. None of this is a promise that you will get access.

Render free web service (render.com/docs/free): spins down after 15 minutes without traffic and takes about a minute to wake. The filesystem is ephemeral, so local files and SQLite are lost on restart or redeploy, and a free web service cannot attach a persistent disk. 750 free instance hours per month. The page says not to use free instances for production. Consequence for this brief: a free web service would lose uploaded videos and job state, and the first request after idle is slow. Plan to keep state in MinIO or another store, and check whether a reviewer waiting a minute is acceptable.
Hugging Face Spaces (huggingface.co/docs/hub/spaces-overview, read 23 Nov 2026): the page says static Spaces are free for everyone, and that Gradio and Docker Spaces run on compute and require a paid plan to create (PRO for personal accounts, Team or Enterprise for organizations). It also says free personal accounts can host up to 2 Gradio Spaces on ZeroGPU. CPU Basic hardware (2 vCPU, 16 GB RAM, 50 GB non-persistent disk) is listed as free, but the same page says creating a compute Space needs the paid plan. The Docker Spaces page (huggingface.co/docs/hub/spaces-sdks-docker) describes Docker Spaces without stating the plan rule. This is what the docs say today; HF may change it, and I did not try to create a Space. I also did not check whether a multi-container Docker Compose app can run there (the Docker page describes one container with one exposed port).
Groq speech to text (console.groq.com/docs/rate-limits): lists whisper-large-v3 and whisper-large-v3-turbo at 20 requests per minute, 2,000 requests per day, 7,200 audio seconds per hour and 28,800 per day. 28,800 seconds is 8 hours of audio per day. That table is labelled as Developer plan base limits, so confirm for your account. The same table lists openai/gpt-oss-120b, openai/gpt-oss-20b and qwen/qwen3.8-27b at 30 requests per minute and 1,000 requests per day, with 8,000 tokens per minute.
Gemini API (aistudio.google.com/docs/pricing): some models, for example gemini-3.8-flash and gemini-3.5-flash-lite, show "Free of charge" input and output on the free tier. Some newer models show the free tier as not available. On the free tier the page says content is used to improve Google products; on the paid tier it says no. The brief is confidential, so do not paste the brief into a free-tier request, and think about whether your test videos or transcripts are fine to send. I did not find per-model free request limits on the pricing page.
pyannote speaker-diarization-3.1 (huggingface.co/pyannote/speaker-diarization-3.1): the model card says the pipeline uses the MIT licence. To download it you must accept the user conditions for it and for pyannote/segmentation-3.0 on Hugging Face and create an access token. The card also says the collected details may be used for emails about paid pyannote products. Remember a deployed container needs that token as a secret, and the reviewers cannot be asked to supply it.
Whisper code (github.com/openai/whisper) and faster-whisper (github.com/SYSTRAN/faster-whisper): the repositories show the MIT licence. Weights not checked, see above.

Before starting autonomous development, create a persistent project instruction and planning system for my "Prompt-Based Video Editing Engine".

Repository: https://github.com/SJLVamsi/-Prompt-Based_Video_Editing_Engine_incubrix.git

Create these files:

- AGENTS.md — permanent engineering rules
- docs/MASTER_GOAL.md — complete project specifications
- docs/ARCHITECTURE.md — technical architecture
- docs/RESEARCH_PLAN.md — research topics and approaches
- docs/FEATURES.md — complete feature breakdown
- docs/ROADMAP.md — phased implementation plan
- docs/progress/MASTER_CHECKLIST.md — all tasks and their status
- docs/progress/CURRENT_STATUS.md — implementation progress
- docs/progress/SESSION_HANDOFF.md — instructions for resuming work
- docs/progress/BLOCKERS.md — unresolved issues
- docs/progress/GIT_LOG.md — verified commit and push history

The project must support core video editing, natural-language editing, FFmpeg, Whisper transcription, silence removal, subtitle generation, semantic scene search, multimodal video understanding, intelligent planning, constraint-aware editing, automatic Shorts/Reels generation, conversational editing, undo/redo, a web-based timeline, and video export.

Use Next.js, React, TypeScript, FastAPI, Python, FFmpeg, OpenCV, and suitable pretrained AI models.

Document every feature, implementation step, research finding, test, bug, and architecture decision in Markdown.

Create small, independently testable tasks. Use specialized agents where available.

After each verified unit of work, commit and push appropriate source and documentation changes to GitHub. Never commit secrets, caches, large media, or model weights.

Build a detailed and executable development roadmap in Markdown. Do not start implementing major features in this setup step.

Inspect the existing repository first, preserve existing work, and commit and push the completed planning documentation.

go through everything that is there , lauch as amany agents as required. Do research on the topic and document everything in .md files and push and commit every change to github.

if you have any doubts , ask me
```

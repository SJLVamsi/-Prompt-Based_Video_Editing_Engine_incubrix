# ROADMAP — Phased Executable Plan

> Do not start major implementation in setup step. This roadmap is the execution order.
> Each phase ends with a verified commit + push. Suggested build order follows brief priority (must-haves → Core → evidence).
> Drop order if late: F18 OpenTimelineIO → F19 60-min target → F20 40-scenario gate.

## Phase 0 — Setup (this session) [CURRENT]
- [x] Inspect repo (empty remote, empty local) — preserve nothing, note Ship60 docs in parent are unrelated.
- [x] Launch 5 research subagents (timeline/FFmpeg, Whisper/VAD, LLM/search, web stack, hosting).
- [ ] Write 11 planning files (this roadmap is one of them).
- [ ] `git init + remote + .gitignore + README skeleton` + commit/push planning docs.
- Exit: `git status` clean, `GIT_LOG.md` has planning commit hash.

## Phase 1 — Timeline schema, history, fixture, pure ops (no video, no AI)
**Goal:** frame-exact core with golden 8-step green.
- 1.1 `engine/schema.py`: frozen `Timeline/Clip/Word/Caption/SourceFingerprint`, `filter_version="v1"`.
  - Test: `test_schema_frozen.py` (mutation raises).
- 1.2 `engine/timebase.py`: `t_to_frame/frame_to_t/frame_to_pts`, `parse_r_frame_rate`.
  - Test: `test_timebase.py` — 24000/1001 vector `144 ↔ 6.006006s`, 10k round-trips, float-naive off-by-one demo.
- 1.3 `engine/hash.py + store.py`: `canonical_json/timeline_hash/source_fingerprint`, save/load.
  - Test: `test_hash.py` — stable across key order/restarts; caption change → new hash.
- 1.4 `engine/words.py`: transcript JSON ingest → frames, `resolve_word_ids`, re-timing tolerance.
  - Test: `test_words.py` — dangling ID raises `DANGLING_WORD_ID`; ±2f re-time preserves intent.
- 1.5 `engine/ops/{cut,keep,speed,caption}.py + validate.py`:
  - Test: `test_ops_cut_keep.py` (empty no-op, zero-length/full-cut errors, overlap coalesce, `keep==cut(complement)` fuzz), `test_ops_speed_caption.py` (bad speed, caption rescale, declash).
- 1.6 `engine/history.py`: undo/redo/restore (undoable restore).
  - Test: `test_history.py` — 5 ops → 5 undos → original hash; unknown hash raises.
- 1.7 Fixture `tests/fixtures/words_10s.json` (10 words, 30fps synthetic) + `test_golden_8step.py` steps 1–5 (no exec): ingest→ops→hashes→graph-string asserts.
  - Exit: `pytest -q` (fast only) green.

## Phase 2 — Transcript + three-way sessions (fixture first, real STT second)
- 2.1 Fixture pipeline: `transcript.json` loader + `cues.py` (words→cues: 1.5–6s, ≤42/line, CPS≤17, 80ms declash) + SRT/VTT writers.
  - Test: golden SRT/VTT (comma vs dot, `WEBVTT` header), corruption cases (null ts, overlap, empty → REVIEW flag).
- 2.2 `session_runner.py`: `translate→validate→execute|clarify|reject`, `results.json/ops_log.jsonl/edl.json/replay.hash`.
  - Test: 3-way matrix (valid/ambiguous/impossible/invalid JSON/overflow) with `MockLLM`.
- 2.3 Silence: word-gap shortener (≥0.5s → 0.3s + 200ms keep) + `silencedetect` preview helper.
  - Test: gap-math + `silencedetect` parity on synthetic.
- 2.4 Real STT (`slow`): `transcribe_svc.py` faster-whisper turbo + VAD (`threshold 0.5, min_silence 500ms, pad 400ms`) + optional align.
  - Test (nightly): tiny-model WER/hallucination on 5 reference audios; VAD sweep note.
- 2.5 Diarization (optional): `diarize.py` pyannote 3.1 + majority-vote reconcile.
  - Test: backchannel/overlap flags; never auto-delete.

## Phase 3 — Renderer (one filter graph)
- 3.1 `engine/render/graph.py` (pure): clips→`trim/atrim/setpts/concat/subtitles/scale` strings + `concat_n` assert.
  - Test: `test_graph_build.py` — contains `trim=start_frame=60:end_frame=300`, `atempo=2.0`, `subtitles`, `concat=n=2` (no binary).
- 3.2 `engine/render/{ffmpeg,presets,captions}.py`: cmd builder, presets (preview/720p/1080p/short), ASS gen, exec + stderr capture.
  - Test (slow): synthetic `testsrc+sine` render → `nb_frames==210±1`, `dur 7.0±0.05s`, `|v-a|<20ms`.
- 3.3 Sync evidence: 23.976 clip + VFR phone clip (normalize `fps+aresample`, `-vsync cfr`); `ffprobe` drift/offset logged; `signalstats/blackdetect + astats/ebur128` detector.
  - Exit: `test_sync_slow.py` green; logs attached to `results.json`.

## Phase 4 — LLM adapter + search + Shorts
- 4.1 `llm_planner.py`: `LLMAdapter` protocol, `MockLLM`, `GroqLLM`, `GeminiLLM`; system <1500 tok; `extra="forbid"` + 1 retry + semantic checks; log `fallback_rate`.
  - Test: fault injection (malformed/overflow/extra keys/placeholders).
- 4.2 `search.py`: SceneDetect→keyframes→CLIP + BGE→`sqlite-vec`/Chroma→timeline-bucket RRF + `why`.
  - Test: seeded query → timestamp + scores.
- 4.3 `shorts.py`: knapsack fit + face-aware 9:16 crop + hook scorer + loudnorm → 3 variants + `hook.json`.
  - Test: over-target fits, 1080×1920, safe margins, LUFS note.
- 4.4 Conversational: `SessionState` + intents; 4-turn script test (refine→undo→hook→restore hash-stable).

## Phase 5 — API + jobs + storage + frontend shell
- 5.1 `schemas.py + contracts/*.schema.json + contracts.ts` parity; `problem+json` errors.
  - Test: `test_contract_parity.py` (Pydantic + Zod same fixture).
- 5.2 Routers `upload/transcribe/plan/edit/render/jobs/export/system`; idempotency (`replay`/`422`); SSE; `healthz/readyz/manifest`.
  - Test: `test_jobs.py` (state machine, replay, mismatch), `test_api_*.py` (httpx, moto, no ffmpeg).
- 5.3 MinIO + Compose: `docker-compose.yml` (api/worker/minio/pg/redis/frontend), `init-buckets.sh`, presigned flow.
  - Test: `compose config` + local smoke (presign→upload→transcribe→plan→render→download).
- 5.4 Frontend: editor shell + timeline + preview + transcript + prompt bar + jobs; `timeline-store/undo-stack/time/sse/api-client`.
  - Test: vitest (time, undo, zod, captions) + Playwright chromium (scrub/cut/undo/caption/SSE/download).

## Phase 6 — Evidence + submission
- 6.1 Batch runner: `scripts/run_sessions.py` (prompt list → sessions) → ≥15 `results.json` incl. failures.
- 6.2 Test pack: fast lane + slow lane + `TESTPACK.md` (what passed/failed + logs).
- 6.3 Live demo: Compose + public URL (or Render demo with MinIO-external note + cold-start warning).
- 6.4 Submission Form + 8-min video (script: insight→math→phone loop→war-room→rejected→24h). Reserve last hours; failed attempts stay in pack.
- Exit: `MASTER_GOAL.md §8` all checked.

## Task Sizing Rule
One task = one file-group + its test + docs update + commit. If a task needs >1 review gate (e.g. graph-build vs exec), split it.

## Estimates (rough, 1 dev + agents)
- P0 (Phases 1–3 + 5.1–5.3): ~60% time. Phase 3 sync evidence is the long pole — do not compress.
- P1 (Phase 4 + 5.4): ~25%. Shorts crop + search index are the long poles.
- Evidence (Phase 6): ~15% + reserve half-day buffer for video/form.

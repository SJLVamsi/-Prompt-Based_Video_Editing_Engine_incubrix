# MASTER_CHECKLIST — All Tasks and Status

> Updated in the same commit as code. Statuses: `[ ] todo`, `[~] in-progress`, `[x] done (hash)`, `[!] blocked`, `[-] dropped with reason`.
> Phases map to `docs/ROADMAP.md`.

## Phase 0 — Setup [~] in-progress
- [x] Inspect local + remote (both empty; parent Ship60 docs unrelated) — 2026-11-23
- [x] Launch 5 research subagents — 2026-11-23
- [x] Write `AGENTS.md`, `MASTER_GOAL.md`, `ARCHITECTURE.md`, `RESEARCH_PLAN.md`, `FEATURES.md`, `ROADMAP.md` — 2026-11-23
- [x] Write progress files (`MASTER_CHECKLIST`, `CURRENT_STATUS`, `SESSION_HANDOFF`, `BLOCKERS`, `GIT_LOG`) + `.gitignore` + `README` skeleton — 2026-11-23
- [x] Commit + push planning docs, record hash in `GIT_LOG.md` — `61963ec` pushed 2026-11-23, `git status` clean, `main...origin/main` in sync

## Phase 1 — Timeline core (no video, no AI) [x] done 2026-11-23 (24 tests green)
- [x] 1.1 `engine/schema.py` + `test_schema_frozen.py`
- [x] 1.2 `engine/timebase.py` + `test_timebase.py`
- [x] 1.3 `engine/hash.py + store.py` + `test_hash.py`
- [x] 1.4 `engine/words.py` + `test_words.py`
- [x] 1.5 `engine/ops/* + validate.py` + `test_ops_*` + fuzz
- [x] 1.6 `engine/history.py` + `test_history.py`
- [x] 1.7 Fixture `words_10s.json` + `test_golden_8step.py` steps 1–5 + `test_graph_build.py`

## Phase 2 — Transcript + sessions [~] in-progress (2.1–2.3 done 2026-11-23, 34 tests green)
- [x] 2.1 `cues.py` + SRT/VTT goldens + corruption tests
- [x] 2.2 `session_runner.py` + 3-way `MockLLM` matrix
- [x] 2.3 Word-gap silence shortener + `silencedetect` preview
- [x] 2.4 `transcribe_svc.py` (turbo+VAD) + nightly STT matrix (slow) — 2026-11-23: `test_transcribe_slow.py` 2 passed (tiny model): 3s silence+VAD → ≤2 words (no hallucination leak); `say` speech → ≥1 word. Compat: `av==16.1.0` pinned (av 19 removed `metadata_errors` kwarg faster-whisper 1.2.1 passes)
- [x] 2.5 `diarize.py` (optional) + vote/relabel — `reconcile_cues` majority-vote + REVIEW flag + graceful missing-dep error; pyannote run stays slow-lane (needs HF_TOKEN)

## Phase 3 — Renderer [x] done 2026-11-23 (43 tests green, ffmpeg 9.0.2 evidence)
- [x] 3.1 `render/graph.py` + `test_graph_build.py` (no binary) + fixed multi-trim input bug (`[vsrc]` → `[0:v]` reuse)
- [x] 3.2 `render/{ffmpeg,presets,probe}.py`: `build_ffmpeg_cmd(input/output)`, `run_cmd`, `timeline_captions_to_ass`, `probe/summarize`; FFmpeg 9 compat (`-fps_mode cfr`, `-vsync` removed upstream)
- [x] 3.3 23.976 + VFR + CFR evidence (`test_sync_slow.py` 3 passed): CFR cut 240f exact / 8.021s / A/V 21ms; 23.976 144f → 6.006s ±0.1; VFR phone normalizes via `fps+aresample`, 6.0s ±0.15

## Phase 4 — LLM + search + Shorts [~] pure parts done 2026-11-23
- [x] 4.1 `llm_adapters.py` (Mock/Groq/Gemini) + `session.py` fault injection (real adapters need keys, slow/manual)
- [x] 4.2 `search.py` keyword fallback + `index.py` vector store + RRF fusion + `scene.py` shot detection (mean-abs-diff, pure + real red→blue cut at f60±2, BGE/CLIP encoder swap next)
- [x] 4.3 `shorts.py` knapsack + 9:16 crop + hook scorer + test
- [x] 4.4 Conversational 4-turn hash-stable test — `test_conversational.py`: refine(cut)→undo→redo→hook(keep)→restore(v1) identical hash, restore undoable

## Phase 5 — API + storage + frontend [x] done 2026-11-23 (full compose green)
- [x] 5.1 `schemas.py` (Pydantic) + `contracts/*.schema.json` + `frontend/lib/contracts.ts` + `test_contract_parity.py` (backend accepts frontend fixtures, rejects dissolve/bad-speed)
- [x] 5.2 Routers MVP — **live-verified vs container**: `healthz ok`, `manifest` presets, `plans:generate` validates (fixed `engine.*` vs `backend.engine.*` import layout bug), `renders` idempotent replay, `jobs` get, `/version`
- [x] 5.3 Full `docker compose up` green — 6/6 `Up` (api, worker, frontend, postgres, redis, s3 healthy); MinIO uninstallable here (Hub repo gone, Quay 401) → LocalStack 4.3 S3, same boto3 code/buckets; buckets created, S3 `smoke-ok` roundtrip, redis `PONG`, pg ready; fixed missing `start` script (`next start`)
- [x] 5.4 Editor shell — **vitest 12/12 + Playwright e2e 1/1 green vs dev AND prod container** (`next start` image): load → ArrowRight step → `C` split 1→2 clips → Undo →1. Fixed real bugs: page import depth `../../` → `../../../`, timecode `formatTC` MM:SS:FF

## Phase 6 — Evidence [~] demo running locally
- [x] 6.1 `scripts/run_sessions.py` → 16 `results.json` (7 done / 7 clarify / 2 reject, incl. failures)
- [x] 6.2 Test pack (`docs/TESTPACK.md`): backend 64 + vitest 12 + e2e 1/1 (dev + prod container) + compose smoke
- [x] 6.3 Live demo: full `docker compose up` on localhost — editor http://localhost:3000/projects/demo, api http://localhost:8000/healthz (6/6 Up; public tunnel optional)
- [ ] 6.4 Submission Form + 8-min video

## P2 Likely-Drop
- [-] Not yet dropped — F18/F19/F20 stay `todo` until P0+P1 verified, then drop explicitly with reason.

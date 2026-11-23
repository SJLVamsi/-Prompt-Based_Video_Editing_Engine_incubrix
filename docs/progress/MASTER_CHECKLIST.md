# MASTER_CHECKLIST — All Tasks and Status

> Updated in the same commit as code. Statuses: `[ ] todo`, `[~] in-progress`, `[x] done (hash)`, `[!] blocked`, `[-] dropped with reason`.
> Phases map to `docs/ROADMAP.md`.

## Phase 0 — Setup [~] in-progress
- [x] Inspect local + remote (both empty; parent Ship60 docs unrelated) — 2026-11-23
- [x] Launch 5 research subagents — 2026-11-23
- [x] Write `AGENTS.md`, `MASTER_GOAL.md`, `ARCHITECTURE.md`, `RESEARCH_PLAN.md`, `FEATURES.md`, `ROADMAP.md` — 2026-11-23
- [x] Write progress files (`MASTER_CHECKLIST`, `CURRENT_STATUS`, `SESSION_HANDOFF`, `BLOCKERS`, `GIT_LOG`) + `.gitignore` + `README` skeleton — 2026-11-23
- [x] Commit + push planning docs, record hash in `GIT_LOG.md` — `61963ec` pushed 2026-11-23, `git status` clean, `main...origin/main` in sync

## Phase 1 — Timeline core (no video, no AI)
- [ ] 1.1 `engine/schema.py` + `test_schema_frozen.py`
- [ ] 1.2 `engine/timebase.py` + `test_timebase.py`
- [ ] 1.3 `engine/hash.py + store.py` + `test_hash.py`
- [ ] 1.4 `engine/words.py` + `test_words.py`
- [ ] 1.5 `engine/ops/* + validate.py` + `test_ops_*` + fuzz
- [ ] 1.6 `engine/history.py` + `test_history.py`
- [ ] 1.7 Fixture `words_10s.json` + `test_golden_8step.py` steps 1–5

## Phase 2 — Transcript + sessions
- [ ] 2.1 `cues.py` + SRT/VTT goldens + corruption tests
- [ ] 2.2 `session_runner.py` + 3-way `MockLLM` matrix
- [ ] 2.3 Word-gap silence shortener + `silencedetect` preview
- [ ] 2.4 `transcribe_svc.py` (turbo+VAD) + nightly STT matrix (slow)
- [ ] 2.5 `diarize.py` (optional) + vote/relabel

## Phase 3 — Renderer
- [ ] 3.1 `render/graph.py` + `test_graph_build.py` (no binary)
- [ ] 3.2 `render/{ffmpeg,presets,captions}.py` + synthetic render test (slow)
- [ ] 3.3 23.976 + VFR evidence (drift + A/V offset logs)

## Phase 4 — LLM + search + Shorts
- [ ] 4.1 `llm_planner.py` (Mock/Groq/Gemini) + fault injection
- [ ] 4.2 `search.py` dual index + RRF query test
- [ ] 4.3 `shorts.py` + 3 variants + `hook.json`
- [ ] 4.4 Conversational 4-turn hash-stable test

## Phase 5 — API + storage + frontend
- [ ] 5.1 `schemas.py` + `contracts/*.schema.json` + `contracts.ts` parity
- [ ] 5.2 Routers + idempotency + SSE + `healthz/readyz/manifest` + `problem+json`
- [ ] 5.3 `docker-compose.yml` + MinIO buckets + smoke
- [ ] 5.4 Editor shell + timeline + transcript + prompt + jobs (vitest + Playwright)

## Phase 6 — Evidence
- [ ] 6.1 `scripts/run_sessions.py` → ≥15 `results.json` incl. failures
- [ ] 6.2 Test pack (`TESTPACK.md`) fast + slow
- [ ] 6.3 Live demo URL (Compose or Render+external store note)
- [ ] 6.4 Submission Form + 8-min video

## P2 Likely-Drop
- [-] Not yet dropped — F18/F19/F20 stay `todo` until P0+P1 verified, then drop explicitly with reason.

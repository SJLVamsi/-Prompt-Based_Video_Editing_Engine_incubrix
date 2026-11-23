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
- [ ] 2.4 `transcribe_svc.py` (turbo+VAD) + nightly STT matrix (slow)
- [ ] 2.5 `diarize.py` (optional) + vote/relabel

## Phase 3 — Renderer [~] graph builder done (test_graph_build green)
- [x] 3.1 `render/graph.py` + `test_graph_build.py` (no binary)
- [ ] 3.2 `render/{ffmpeg,presets,captions}.py` + synthetic render test (slow)
- [ ] 3.3 23.976 + VFR evidence (drift + A/V offset logs)

## Phase 4 — LLM + search + Shorts [~] pure parts done 2026-11-23
- [x] 4.1 `llm_adapters.py` (Mock/Groq/Gemini) + `session.py` fault injection (real adapters need keys, slow/manual)
- [x] 4.2 `search.py` keyword fallback + RRF-ready test (embedding index sqlite-vec/Chroma next)
- [x] 4.3 `shorts.py` knapsack + 9:16 crop + hook scorer + test
- [ ] 4.4 Conversational 4-turn hash-stable test

## Phase 5 — API + storage + frontend [~] MVP skeleton done 2026-11-23
- [x] 5.1 `schemas.py` (Pydantic) + `contracts/*.schema.json` + `frontend/lib/contracts.ts` (parity CI next)
- [x] 5.2 Routers MVP: `healthz/readyz/manifest/version`, `plans:generate`, `renders` + idempotency replay, `jobs` + cancel, SSE stub + `test_api.py`
- [x] 5.3 `docker-compose.yml` + `.env.example` (smoke test next, needs docker)
- [ ] 5.4 Editor shell + timeline + transcript + prompt + jobs (scaffold `Timeline.tsx/contracts/undo-stack`; vitest + Playwright next)

## Phase 6 — Evidence [~] batch runner done
- [x] 6.1 `scripts/run_sessions.py` → 16 `results.json` (7 done / 7 clarify / 2 reject, incl. failures)
- [x] 6.2 Test pack (`docs/TESTPACK.md`) fast lane 40 green; slow lane pending ffmpeg/weights
- [ ] 6.3 Live demo URL (Compose + public URL; Docker available next)
- [ ] 6.4 Submission Form + 8-min video

## P2 Likely-Drop
- [-] Not yet dropped — F18/F19/F20 stay `todo` until P0+P1 verified, then drop explicitly with reason.

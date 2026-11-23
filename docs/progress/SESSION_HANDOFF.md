# SESSION_HANDOFF — How to Resume Work

> Read this + `CURRENT_STATUS.md` + `MASTER_CHECKLIST.md` at session start. `AGENTS.md` overrides on conflict.

## 1. Where We Are (2026-11-23)
Phase 0 planning. All 5 research briefs integrated into `docs/*.md`. No engine/API/frontend code yet (intentional — setup step builds docs only).

## 2. Repo State
- Local: `/Users/vamsisatuluri07/Documents/incubrix_placement` (`main`, remote `origin` = GitHub URL above).
- Remote was empty; planning commit is the first commit (see `GIT_LOG.md` for hash).
- Layout: `AGENTS.md`, `docs/{MASTER_GOAL,ARCHITECTURE,RESEARCH_PLAN,FEATURES,ROADMAP}.md`, `docs/progress/*`, `backend/`, `frontend/` (empty placeholders).

## 3. Resume Commands
```bash
cd /Users/vamsisatuluri07/Documents/incubrix_placement
git status --short && git log --oneline -5
cat docs/progress/CURRENT_STATUS.md docs/progress/BLOCKERS.md
# start next task (Phase 1.1):
pytest -q  # expect: no tests collected (until 1.1 lands)
```

## 4. Next Task Pointer
- `MASTER_CHECKLIST.md`: Phase 1.1 `engine/schema.py` + `test_schema_frozen.py`.
- Follow `ROADMAP.md` Phase 1 order; TDD (red→green), update `CURRENT_STATUS` + `MASTER_CHECKLIST` + `GIT_LOG` in same commit, push.

## 5. Context to Reload
- `AGENTS.md` §§1–6 (five non-negotiables, contracts-first, frame math, FFmpeg, STT, LLM).
- `ARCHITECTURE.md` §2 (Timeline schema) + §3 (backend layout).
- Research details: `RESEARCH_PLAN.md` R1–R4 for Phase 1; R8 for Phase 2.2.

## 6. Gotchas
- Never store `23.976` as float; use `Fraction(24000,1001)`.
- Never `-c copy` for edits; always single re-encode graph.
- Engine tests must run without STT (fixture first).
- Mock LLM in all fast tests; real Groq/Gemini slow/manual only + `--allow-free-tier` gate.
- Vendor limits are snapshots — re-check live pages listed in `RESEARCH_PLAN.md` R9/R14 before depending on numbers.
- Do not ask reviewers to supply HF token; container reads env secret.

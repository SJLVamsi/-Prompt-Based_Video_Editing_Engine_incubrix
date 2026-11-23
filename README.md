# Prompt-Based Video Editing Engine

Natural-language video editing: upload → transcribe → prompt → frame-accurate render → web timeline → export.
`Next.js + React + TypeScript + FastAPI + Python + FFmpeg + OpenCV + pretrained AI`.

**Status:** Phase 0 planning (docs only, no implementation yet — see `docs/ROADMAP.md`).

## Docs (source of truth)
- `AGENTS.md` — permanent engineering rules
- `docs/MASTER_GOAL.md` — spec + acceptance
- `docs/ARCHITECTURE.md` — system design
- `docs/RESEARCH_PLAN.md` — research topics + findings
- `docs/FEATURES.md` — feature breakdown (P0/P1/P2)
- `docs/ROADMAP.md` — phased executable plan
- `docs/progress/` — `MASTER_CHECKLIST.md`, `CURRENT_STATUS.md`, `SESSION_HANDOFF.md`, `BLOCKERS.md`, `GIT_LOG.md`

## Quickstart (after Phase 5 lands)
```bash
cp .env.example .env   # (to be added in Phase 5)
docker compose up
# frontend http://localhost:3000  api http://localhost:8000  minio http://localhost:9001
```

## Rules in brief
- Frame `int` + `Fraction(fps_num/fps_den)`; word-ID anchors; no float drift.
- Single FFmpeg `-filter_complex` re-encode; no `-c copy` cuts.
- LLM = translator only (Pydantic/Zod + `results.json` + replay hash).
- Fixture-first STT; VAD + padding; diarization advisory only.
- Small testable tasks; commit + push + docs update per unit. See `AGENTS.md`.

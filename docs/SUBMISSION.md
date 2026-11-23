# SUBMISSION — Demo Script, Video Shot List, Form Answers

> 6.4 needs a human: record the 8-minute video and submit the form. Everything
> below is ready to read/film/submit. Failed attempts stay in `docs/TESTPACK.md`
> and `docs/progress/BLOCKERS.md` — the brief scores honest failures over hidden ones.

## Demo URLs (local, stack running via `docker compose up`)
- Editor: http://localhost:3000/projects/demo
- API health: http://localhost:8000/healthz
- API manifest: http://localhost:8000/manifest

## 8-Minute Video Shot List
1. **0:00–1:00 The insight** — timing is the #1 risk (sync drift, VFR phone, word times). Show `AGENTS.md` five non-negotiables.
2. **1:00–2:00 Frame math** — `t_to_frame` Fraction demo; `pytest test_timebase` green; float `0.1+0.2 != 0.3`.
3. **2:00–3:30 Phone loop** — upload note → `words_10s.json` fixture → prompt "cut silences, keep demo" → `results.json` (7 done / 7 clarify / 2 reject across 16 sessions).
4. **3:30–5:00 Editor** — live http://localhost:3000/projects/demo: ArrowRight step, `C` split, Undo; transcript word click seeks.
5. **5:00–6:00 Render evidence** — 23.976 + VFR phone: 240f exact, 8.021s, A/V 21ms; `test_sync_slow.py` 3 passed.
6. **6:00–7:00 STT honesty** — silence+VAD suppresses hallucinations; real adapters need keys (Mock default); av-19 incompatibility found live and pinned.
7. **7:00–8:00 Rejected + 24h** — dropped P2 (OTIO/60-min/40-scenario) with reason; with 24h: arq worker tasks, pgvector index, Shorts crop UI.

## Form Answers (paste + attach)
- Repo: https://github.com/SJLVamsi/-Prompt-Based_Video_Editing_Engine_incubrix
- Stack: Next.js 14 + React 18 + TS + FastAPI + FFmpeg 9 + faster-whisper + OpenCV + LocalStack S3.
- Must-haves: frame ints + Fractions, word-ID anchors, single filter-graph re-encode, LLM-as-translator with schema, distrusted STT.
- Evidence: `pytest -q` 64 passed; vitest 12/12; Playwright 1/1 (dev + prod); 16 `results.json`; compose 6/6 Up; `docs/TESTPACK.md`.
- Known gaps: real Groq/Gemini keys not wired (Mock default), pyannote needs HF_TOKEN, public tunnel not set up, video/form need human.

## Pre-Submit Checklist
- [ ] `docker compose up` → 6/6 Up, editor + healthz reachable
- [ ] `python3 -m pytest -q` → 64 passed; `npx vitest run` → 12; `npx playwright test` → 1
- [ ] Record 8-min video from shot list above
- [ ] Submit form + attach video + repo link

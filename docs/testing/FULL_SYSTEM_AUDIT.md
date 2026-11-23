# FULL_SYSTEM_AUDIT — Complete Verification (2026-11-23)

## 1. Environment — PASS
- arm64 Apple Silicon, 16 GB RAM, macOS 27.2.1, Python 3.13.10, Node v24.17.0/npm 11.13.0.
- FFmpeg + FFprobe 9.0.2 (Homebrew). Docker Desktop 4.79.0, daemon responding.
- Deps: fastapi 0.141.1, pydantic 2.13.4, faster-whisper 1.2.1 (+`av==16.1.0` pin), cv2 5.1.0, boto3 1.44.9, numpy 2.5.0.
- Notes: (a) objc duplicate-lib warnings (av vs cv2 `libavdevice`) — no crash observed; (b) local `.env` was stale (minio) → refreshed from `.env.example`; (c) brew FFmpeg lacks libass+freetype (see §4).

## 2. Backend — PASS (scoped)
- `pytest -q`: **66 passed**. Live container: healthz/manifest/version 200; `plans:generate` valid 200 + invalid 422; `renders` idempotent replay; `jobs` get.
- Missing routers (upload/transcribe/projects/download) documented as MISSING, not claimed.

## 3. Frontend — PASS (scoped)
- vitest **12/12**; Playwright **2/2** vs dev AND prod container.
- Fixed live: page import depth, `formatTC` timecode, missing `start` script, absent `/api/proxy` route (was silent 404), silent prompt errors (now visible `role=status`).

## 4. Video engine — PASS with one BLOCKED path
- Trims/splits (multi-segment), speed (atempo chains), concat, CFR/VFR, 9:16 crop, ASS/SRT/VTT generation, soft-sub mux — all executed and probed.
- Cropping/resizing verified via Shorts render; transitions/filters not implemented (MISSING, not claimed).
- **BLOCKED**: text burn-in (`subtitles`/`ass`/`drawtext` absent in brew FFmpeg 9) → `require_text_burnin()` guard + sidecar/soft-sub path verified.

## 5. AI engine — PASS (scoped)
- Live: `say`→tiny→9 words→search 1.0→keep→render (workflow B). VAD silence→≤2 words. Scene cut at f60±2. Index KNN + RRF. 4-turn conversational hash-stable.
- BLOCKED without keys: Groq/Gemini adapters (unit-tested interface, free-tier gate kept). turbo-model benchmarks not run.

## 6. E2E — see E2E_RESULTS.md (B/C/D/E/F PASS, A PARTIAL)
## 7. Security/Performance — see SECURITY_AUDIT.md / PERFORMANCE_REPORT.md (no vulns found; no auth by design for local demo)
## 8. Tests — 66 pytest + 12 vitest + 2 e2e green; `tsc` via `next build` green (prod image built)
## 9. Status — see FEATURE_TEST_MATRIX.md
## 10. Fixes this audit
1. `.env` stale minio values → refreshed; compose overrides documented.
2. Missing `/api/proxy/[...path]` route (silent 404) → implemented + `API_INTERNAL_URL` for in-compose networking.
3. Silent prompt failures → visible `role=status` errors; e2e covers it.
4. Burn-in cryptic FFmpeg failure → `require_text_burnin()` + `ffmpeg_has_filter()` + tests.
5. E2E placeholder/selector bugs fixed (aria-label).

## Startup commands
```bash
docker compose up -d            # 6/6: http://localhost:3000 http://localhost:8000
python3 -m pytest -q            # 66 passed
cd frontend && npx vitest run   # 12 passed
npx playwright test             # 2 passed (needs :3000 + API :8000)
```

## Unresolved (need user)
- Submission Form + 8-min video (6.4) — human filming/submission.
- Public demo URL needs tunnel opt-in.
- Real LLM keys (Groq/Gemini) + HF_TOKEN for pyannote full runs.

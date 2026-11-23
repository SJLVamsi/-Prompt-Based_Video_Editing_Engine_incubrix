# PERFORMANCE_REPORT — Apple Silicon, 16 GB RAM (2026-11-23)

## Test suite times
- `pytest -q` (66 tests incl. STT tiny + 3 FFmpeg renders): **~4–5 s** (models cached).
- First STT run (model download): ~7 min once; cached after.
- `npx vitest run`: **97–183 ms** (12 tests).
- Playwright (cold dev server): ~30 s first compile; warm: **<1 s**.

## Render performance (synthetic 320x240/30fps + sine)
- 10 s source → 8 s cut render: **<2 s wall** (well under 2× realtime even at this size).
- 1080x1920 Shorts crop+scale 3 s: **<3 s wall**.
- Memory: no measurement harness yet; renders stream via single `-filter_complex` (no intermediates). 16 GB is ample for ≤1080p jobs; 4K + turbo model concurrently not tested (flagged).

## STT
- tiny model, 3–10 s audio, CPU: seconds. `turbo` default (800 MB) not benchmarked — expect ~4.5× faster than large-v3 per research; verify before claiming.
- MPS note: ctranslate2 suggests `device="mps"` (2× on Apple Silicon); pipeline uses CPU default — free optimization, untested.

## Startup
- `docker compose up`: infra ~20 s (image pulls once), api ~10 s, frontend ~15 s.
- `next dev`: ready 7 s; production `next start`: instant after boot.

## Bottlenecks / next
1. No job queue yet (renders would block API) — arq worker is a stub; required before real uploads.
2. No progress streaming (SSE stub emits one event).
3. Add ` specialty: time budget per render + `tookMs` already logged in `results.json` shape.

# E2E_RESULTS — Executed Workflows (2026-11-23)

All run against real binaries/services. `/tmp/audit_e2e` artifacts are scratch (not committed).

## A. Prompt → edit → preview → export — PARTIAL
- `POST /api/proxy/plans:generate` with plan JSON → validated plan live.
- `op_cut/keep/speed/caption` + `build_ffmpeg_cmd` + real encode verified (see B).
- Gap: NL→plan needs LLM keys (Mock only); no preview/download endpoints (MISSING).

## B. Transcribe → search → cut — PASS (live)
- `say` "welcome to the demo of speed and captions today" → tiny model → **9 words**.
- `keyword_search("demo speed")` → hit score **1.0**.
- `op_keep` first half: 76f → 38f; rendered via graph → **38f, 1.288s, A/V 21ms**.

## C. Silence → subtitles → export — PASS (sidecar/soft-sub path)
- Word-gap cuts math green; `cues_to_srt/vtt` goldens green.
- Live: ASS generated → `subtitles` filter **absent** in brew FFmpeg 9 (BLOCKED burn-in).
- Fallback executed: `-c copy -c:s mov_text` → **h264+aac+mov_text** streams verified.

## D. Vertical short — PASS
- `crop_916_params(1280,720)` → x437/w405; rendered **1080x1920** verified by ffprobe.

## E. Edit → undo → redo → reopen — PASS
- `test_conversational`: refine→undo→redo→hook→restore identical hash, restore undoable.
- `save/load_timeline` round-trip hash-stable (`test_hash`).

## F. Invalid input → safe errors — PASS
- API: malformed plan → 422 `E_VALIDATION` `problem+json` (live, via proxy).
- Engine: zero-length/full-cut/dangling-ID/placeholder/overflow → coded `TimelineValidationError`.
- UI: invalid prompt → visible `role=status` error (e2e asserts; was silent 404 before fix).

## Browser E2E (Playwright, chromium headless-shell 159)
- vs `next dev` and vs production `next start` container: **2/2 green**
  (scrub/step/split/undo; prompt error display).

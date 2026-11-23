# UAT — Real-World Acceptance Run (2026-11-23)

Prompt under test: **"Remove silent parts, add English subtitles, and convert to 9:16"**

## Sample media (real, generated for the run)
- 3× `say -v Samantha` phrases + 2× 1.5 s `anullsrc` gaps, concat → `speech.wav` 7.71 s.
- `testsrc=640x480@30` + speech → `sample.mp4` (h264 + aac, 7.714 s). Kept in `/tmp/uat` (scratch, not committed).

## Workflow executed (browser-driven, Playwright chromium vs compose stack)
1. `GET /uat` → 200. File input `setInputFiles(/tmp/uat/sample.mp4)` → `POST /api/proxy/uploads` → **"Uploaded sample.mp4: 7.71s, 640x480"**.
2. Transcribe → tiny model → **"Transcribed 9 words"** (`welcome to the demo of speed and captions today`).
3. Apply prompt → `POST /api/proxy/uat/run` → **"Done: cut-silence:2, subtitles:3-cues, vertical:1080x1920"**.
4. `<video src="/api/proxy/exports/{jobId}/download">` present; download link works.

## Output verification (ffprobe on downloaded MP4)
- Container: h264 + aac + **mov_text** subtitle streams.
- Duration **5.675 s** (source 7.714 s → −2.04 s = both 1.5 s gaps shortened to 0.3 s).
- Resolution **1080x1920** (9:16 crop+scale of 640x480 verified).
- A/V offset in renders ≤21 ms (see `test_sync_slow`).

| Requested operation | Evidence it worked |
|---|---|
| Remove silent parts | `cut-silence:2`; 7.714 s → 5.675 s; filters `atrim`/`trim` in graph |
| English subtitles | 3 cues → SRT sidecar + muxed `mov_text` stream present in output |
| Convert to 9:16 | `crop=…:scale=1080:1920`; ffprobe `width=1080 height=1920` |

## Bugs found and fixed during this UAT
1. `RuntimeError: python-multipart not installed` → API crash on upload. Fixed: pinned `python-multipart==0.0.20`, rebuilt image.
2. `FileNotFoundError: ffprobe` → slim image lacks FFmpeg. Fixed: `apt-get install ffmpeg` in both Dockerfiles. Side win: Debian build **has libass** (`subtitles`/`ass` present) — burn-in possible in-container.
3. `vf_video_tail` appended to whole filtergraph would have attached crop to the **audio** chain. Fixed: `build_graph(..., vf_video_tail)` splices into video chain before `[vout]` (additive param, old tests unchanged).
4. Proxy crashed on non-JSON upstream errors (`res.json()` throw → silent UI). Fixed: `parseBody` with raw-text fallback + visible `role=status` errors.
5. `require_text_burnin` branch in `uat/run` could ship caption-less output where libass exists. Fixed: deterministic soft-sub mux everywhere; burn-in documented as env-dependent.

## Remaining limitations (honest)
- Transcribe default in code says `turbo`; UAT ran `tiny` (fast, cached). Turbo not benchmarked here.
- Uploads/renders live in container `/tmp` (ephemeral) — S3 wiring exists (`S3_ENDPOINT`) but the UAT slice doesn't use it yet.
- No auth/rate limits (local demo scope). No progress streaming (sync requests; 7 s media ≈ seconds).
- Burn-in blocked on Homebrew FFmpeg (no libass/freetype); works in Debian image but UAT uses soft-sub for determinism.
- NL understanding is keyword-intent, not LLM planning (Groq/Gemini keys still required for that path).
- Public URL: none (localhost only). Submission video + form still human tasks.

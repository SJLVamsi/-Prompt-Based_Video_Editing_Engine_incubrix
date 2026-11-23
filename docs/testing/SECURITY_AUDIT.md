# SECURITY_AUDIT — Safe Tests Only (2026-11-23)

## Command injection — PASS
- `run_cmd` uses argv lists, never `shell=True` (verified by grep + all renders executed).
- Filter strings interpolate only ints/enums; caption text goes to ASS files (`,`-safe, `\n`→`\N`).

## Secrets — PASS
- `grep` for `sk-`, private keys, tokens in `backend frontend contracts scripts infra docker-compose.yml`: only env-var **reads** (`GROQ_API_KEY`, `GOOGLE_API_KEY`, `HF_TOKEN`); no hardcoded secrets.
- `.env` gitignored and clean (`git ls-files` shows no `.env`); `.env.example` holds placeholders only.
- Gemini free-tier guard: `ALLOW_FREE_TIER=1` required, `ALLOW_FREE_TIER=0` default.

## Paths/files — PASS with note
- Render I/O uses explicit `input_path/output_path` (tests use `tmp_path`); no user-controlled absolute paths reach the API (no upload router exists → nothing to traverse; MISSING upload must enforce this when built).
- `subtitles=` path in graph is a fixed `caps.ass` filename (no user input).
- Timeouts: `run_cmd(timeout=180)`, `probe(timeout=60)`, LLM `urlopen(timeout=30)`.
- Tmp cleanup: pytest `tmp_path` auto-cleaned; `/tmp/audit_e2e` is manual scratch, outside repo.

## Failure handling — PASS
- `require_text_burnin()` converts missing-filter renders into actionable errors (not cryptic FFmpeg dumps).
- `transcribe_file`/`diarize_file` raise clean `RuntimeError` when weights/token absent (no silent fallback).
- Worker stub idles with a logged warning (no fake success).

## Open items (not vulnerabilities, tracked)
- No auth/rate-limiting on API (local demo scope; required before any public deploy).
- No upload validation yet (no upload endpoint; add allowlist + size cap + `ffprobe` gate when built).

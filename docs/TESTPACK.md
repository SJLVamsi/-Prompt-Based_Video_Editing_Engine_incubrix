# TESTPACK — Evidence (fast lane green, slow lane pending hardware)

## Fast lane (`pytest -q`) — 2026-11-23: 40 passed
- `test_schema_frozen`, `test_timebase` (23976 vector, float-drift demo), `test_hash` (stable + caption change),
  `test_words` (frames, dangling, retiming), `test_ops_cut_keep` (noop, zero/full, coalesce, keep==cut complement fuzz),
  `test_ops_speed_caption`, `test_history` (5 undo/redo, unknown restore, undoable restore),
  `test_golden_8step` (ingest→cut/speed/caption→hashes→graph strings→undo/restore),
  `test_graph_build`, `test_cues` (SRT comma vs VTT dot + WEBVTT), `test_session` (3-way matrix),
  `test_silence`, `test_api` (health/manifest, validation 422, idempotency replay), `test_smart` (hook/fit/crop/search).

## Batch sessions — 16 runs in `sessions/run_*/results.json`
- `7 done / 7 clarify / 2 reject` (counts via `grep status`). Includes honest failures:
  malformed JSON, overflow timestamps, extra keys, placeholder text.
- Replay: same ops → same `replay_hash` (`sha256(source|canonical_plan|engine_version)`).

## Slow lane (not yet run — needs ffmpeg + weights + GPU)
- `test_sync_slow`: 23.976 + VFR phone render, drift <1.5 frames, A/V <20ms.
- `transcribe_svc` nightly: tiny-model WER/hallucination matrix, VAD sweep.
- Playwright chromium: scrub/cut/undo/caption/SSE/download.

## Logs
- `pytest -q`: 40 passed in 0.08s (see commit message).
- `scripts/run_sessions.py` (PYTHONPATH=.): wrote 16 sessions, status split above.

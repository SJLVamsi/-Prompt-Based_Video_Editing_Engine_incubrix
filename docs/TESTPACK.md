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

## Slow lane — 2026-11-23 GREEN (ffmpeg 9.0.2)
- Render (`pytest backend/tests/test_sync_slow.py`: 3 passed).
- STT (`pytest backend/tests/test_transcribe_slow.py`: 2 passed, tiny model): 3s `anullsrc` silence + VAD → ≤2 words (hallucination suppressed); macOS `say` "hello demo captions today" → ≥1 word transcribed. Env fix: `av==16.1.0` pinned in `requirements.txt` (av 19 drops `metadata_errors` kwarg faster-whisper 1.2.1 passes to `av.open`; av 14.x has no py3.13 wheel).
- Conversational (`test_conversational.py`): refine→undo→redo→hook→restore hash-stable, restore undoable.
- Diarize (`test_diarize.py`): majority-vote + REVIEW flag; clean RuntimeError when pyannote missing.
- Fast lane total: 49 passed.
- Frontend (`npx vitest run` in `frontend/`, 2026-11-23): **12/12 green** — `time` (round-trip, snap, TC, 23976), `undo-stack` (round-trip, empty, clear-future, cap-100), `contracts` (valid cut, reject dissolve/bad speed/empty caption; mirrors backend parity cases). Env fix: `typescript@5.4.0` does not exist → pinned `5.4.5`.
- `test_cfr_length_and_av_offset`: synthetic 10s testsrc 30fps+sine → cut head 60f → **240 frames exact**, duration **8.021s** (expect 8.0), A/V offset **21ms** (<40ms gate).
- `test_23976_roundtrip_frames`: 24000/1001 source → 144f render → duration ≈6.006s ±0.1, A/V <40ms.
- `test_vfr_phone_normalizes_to_cfr`: `-fps_mode vfr` source → graph `fps+aresample` → 6.0s ±0.15 render.
- Compat note: FFmpeg ≥7 deprecates `-vsync`; FFmpeg 9 removes it. Cmd builder + VFR fixture now use `-fps_mode cfr/vfr`.

## Logs
- `pytest -q`: 40 passed in 0.08s (see commit message).
- `scripts/run_sessions.py` (PYTHONPATH=.): wrote 16 sessions, status split above.

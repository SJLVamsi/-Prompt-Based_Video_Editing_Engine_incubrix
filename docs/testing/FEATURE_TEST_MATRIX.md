# FEATURE_TEST_MATRIX — Verdict per Feature (evidence-linked)

Legend: **PASS** = executed green. **PARTIAL** = partly verified, gaps noted.
**FAIL** = reproduced bug (fixed or open). **MISSING** = not implemented.
**BLOCKED** = needs external key/binary/service.

## P0 Must-Haves
| # | Feature | Verdict | Evidence |
|---|---|---|---|
| 1 | 1-frame sync, no clipped words | PASS | `test_sync_slow` 3/3; CFR 240f exact, 8.021s, A/V 21ms; 23.976 + VFR green |
| 2 | Frame ints + Fractions + word-ID anchors | PASS | `test_timebase`, `test_words`, golden 8-step; float-drift demo tests |
| 3 | Single filter-graph re-encode | PASS | `test_graph_build`, `test_golden_8step`; real renders via `build_ffmpeg_cmd` |
| 4 | LLM translator-only + schema + replay hash | PASS | `test_session` 3-way matrix; 16 `results.json`; `replay_hash` deterministic |
| 5 | Distrusted STT (VAD + padding + gating) | PASS | `test_transcribe_slow` 2/2 (silence→≤2 words, `say`→≥1 word); `test_silence` |

## P1 Core
| Feature | Verdict | Evidence |
|---|---|---|
| cut/keep/speed/caption pure ops | PASS | `test_ops_*`, fuzz `keep==cut(complement)` |
| undo/redo/restore | PASS | `test_history`, `test_conversational` 4-turn, e2e Undo button |
| Transcript fixture (no-STT engine) | PASS | `words_10s.json` drives golden test |
| Real STT faster-whisper turbo+VAD | PARTIAL | tiny-model verified; `turbo` default untested (800MB download, 16GB RAM OK but not run) |
| Silence removal (word-gap) | PASS | `test_silence` gap math; `silencedetect` preview args |
| Subtitles SRT/VTT + ASS export | PASS | `test_cues` goldens (`,` vs `.`, `WEBVTT`) |
| Soft-sub mux (mov_text) | PASS | live: h264+aac+mov_text streams verified 2026-11-23 audit |
| Caption burn-in (`subtitles`/`ass`/`drawtext`) | BLOCKED | brew FFmpeg 9.0.2 lacks libass+freetype (`Unknown filter`); `require_text_burnin()` guard + `test_burnin_guard` 2/2; sidecars/soft-sub are the working path |
| Semantic search (keyword + vector + RRF) | PASS | `test_smart`, `test_index` 5/5; live `say`→transcribe→search→cut→render verified |
| Scene detection | PASS | `test_scene` 5/5 (pure + real red→blue cut at f60±2) |
| Shorts knapsack + 9:16 crop + hook | PASS | `test_smart`; live 1280x720→1080x1920 crop render verified |
| Conversational editing | PASS | 4-turn hash-stable test; undo/redo are log-pointers (no LLM call) |
| Web timeline | PASS | vitest 12/12 + e2e scrub/cut/undo vs dev AND prod container |
| Prompt submit + error display | PASS | proxy route live 422 `E_VALIDATION`; e2e asserts visible error (fixed silent 404) |
| Video export presets + thumbs | PARTIAL | presets asserted in cmd builder + manifest; real preset encode + thumbs not run |
| Jobs + idempotency + SSE | PARTIAL | state machine unit + live replay test; SSE endpoint streams stub event only |

## API Surface (audited live vs container 2026-11-23)
| Endpoint | Verdict | Evidence |
|---|---|---|
| `GET /healthz /readyz /manifest /version` | PASS | `curl` 200 live |
| `POST /v1/plans:generate` | PASS | valid 200 + invalid 422 `E_VALIDATION` live |
| `POST /v1/renders` + `Idempotency-Key` | PASS | same jobId replay live |
| `GET/POST /v1/jobs/{id}[/cancel]` + SSE | PASS (cancel/smoke) | live get; cancel covered by unit only |
| Upload / transcribe / projects / download routers | MISSING | never implemented; MVP serves fixture+synthetic inputs |

## Dropped (explicit, with reason)
OTIO export, 60-min latency target, 40-scenario CI gate — brief scores only on full-level verification; out of scope.

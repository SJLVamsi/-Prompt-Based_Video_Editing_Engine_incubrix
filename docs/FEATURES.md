# FEATURES — Complete Breakdown

> Every feature: ID → description → acceptance (testable) → depends on → phase.
> P0 = must-have (judged first). P1 = Core. P2 = likely-drop (10/100 marks only if fully verified).

## P0 — Must-Haves

### F01. Timeline schema + history + hashes
- Immutable `Timeline{fps_num,fps_den,clips,captions,words,version,parent_hash,timeline_hash,fingerprint}`; `History` undo/redo/restore; `source_fingerprint`.
- Accept: no-video unit tests green; same timeline → same hash across restarts; `restore(unknown)` → `KeyError`.
- Phase 1.

### F02. Transcript fixture input (no STT)
- Saved `transcript.json{words,segments,meta}` as first engine input; engine never imports STT.
- Accept: golden 8-step runs with fixture only.
- Depends F01. Phase 1.

### F03. Pure ops: cut/keep/speed/caption/undo/redo/restore
- `op_cut/keep/speed/caption_add`, `history undo/redo/restore`; validate codes (`EMPTY_TIMELINE, OUT_OF_BOUNDS, ZERO_LENGTH, BAD_SPEED, DANGLING_WORD_ID`); normalize sort/coalesce.
- Accept: 8-step worked example green; fuzz `keep==cut(complement)`; speed rescale captions.
- Depends F01–F02. Phase 1.

### F04. Three-way answers + session runner
- `EditPlan.response ∈ {results,clarify,reject}`; `session_runner` writes `results.json + ops_log.jsonl + edl.json + replay.hash`.
- Accept: ≥15 sessions covering all three ways; replay same ops → same hash.
- Depends F03. Phase 2.

### F05. Single-graph renderer
- `graph.py` (pure) + `ffmpeg.py` (exec) + `presets.py`; `trim=start_frame` / `atrim` sec + `setpts` → `concat` → `format/subtitles/scale` → `libx264+aac+faststart+CFR`.
- Accept: 23.976 clip + phone VFR clip measured: drift <1.5 frames, A/V <20ms; graph string logged.
- Depends F01–F03. Phase 3.

### F06. LLM adapter (mock + real) with schema validation
- `LLMAdapter` protocol; `MockLLM` golden; Groq/Gemini behind same interface; Pydantic `extra="forbid"` + 1 retry + semantic checks.
- Accept: fault-injection matrix green (malformed, overflow, extra keys); fallback rate logged.
- Depends F04. Phase 4.

### F07. HTTP API + jobs + idempotency + errors + health + manifest
- `/v1` routers (upload/transcribe/plan/edit/render/jobs/export/system); `problem+json`; `Idempotency-Key`; SSE events; `healthz/readyz/manifest/version`.
- Accept: contract parity CI; replay/mismatch tests; `/readyz` degraded mock.
- Phase 5.

### F08. Real STT with VAD
- faster-whisper `turbo` + `vad_filter` + padding + confidence gating; alignment optional.
- Accept: nightly WER/hallucination matrix; fixture suite still green without weights.
- Depends F02. Phase 2 (after fixture).

## P1 — Core

### F09. Silence removal
- Word-gap primary (≥0.4–0.8s → 0.3s + 200ms keep, 120ms pad, 80ms declash); `silencedetect` preview.
- Accept: gap-math tests + AB naturalness note.

### F10. Subtitle generation
- Words→cues (1.5–6s, ≤42/line, CPS≤17) → SRT/VTT/ASS; burn-in filter; soft-sub mux.
- Accept: golden SRT/VTT; OCR spot on burn-in.

### F11. Semantic scene search
- Shot chunk (SceneDetect) + BGE + CLIP dual index (`sqlite-vec`/Chroma); timeline-bucket RRF.
- Accept: `"where she explains pricing"` → timestamp + `why` scores.

### F12. Multimodal understanding
- Keyframes → CLIP embed + vision-LLM captions top-K.
- Accept: caption file + search recall note.

### F13. Intelligent planning + constraint-aware fit
- Knapsack duration fit; platform constraints; loudnorm.
- Accept: over-target prompt fits without speech >1.3×.

### F14. Auto Shorts/Reels
- Hook + beats + CTA → 9:16 face-aware crop + burned captions + 3 variants + `hook.json`.
- Accept: 1080×1920, ≤60s, safe margins, loudnorm verified.

### F15. Conversational editing
- `SessionState` + intents (`refine|undo|redo|restore|clarify`); pronoun resolution via `last_results`.
- Accept: 4-turn script (refine→undo→hook→restore) hash-stable.

### F16. Web timeline
- V1/A1/C1 tracks, waveform, RAF playhead, word-link, drag cuts, keyboard, undo-stack-100.
- Accept: Playwright scrub/cut/undo + caption edit + SSE progress.

### F17. Video export
- Presets preview/720p/1080p/short; thumbs + storyboard; 302 presigned download.
- Accept: `qt-faststart` atom + AAC present; byte check.

## P2 — Likely to Drop First

### F18. OpenTimelineIO export — drop unless all P0+P1 verified.
### F19. 60-min latency target — drop; log `tookMs` instead.
### F20. 40-scenario CI gate — drop to fast/slow lanes (fast PR <5min, slow nightly).

## Cross-Cutting

- **F21. Docker Compose + MinIO batch runner** (P0 infra): one-command up; `init-buckets.sh`; seed demo. Accept: smoke green.
- **F22. Live demo + 15 sessions + test pack + Submission Form + 8-min video** (P0 evidence). Accept: checklist in `MASTER_GOAL.md §8`.
- **F23. Docs-as-code**: every feature updates `FEATURES/ROADMAP/CHECKLIST/CURRENT_STATUS` in same commit.

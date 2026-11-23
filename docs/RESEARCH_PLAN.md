# RESEARCH_PLAN — Topics, Approaches, Status

> Each topic: question → approach → where result lands. Check off when doc/code updated.
> Vendor limits change — re-read page before depending on a number.

## R1. Frame-Accurate Timing [DONE — researched 2026-11-23]
- Q: How to avoid sync drift across many cuts? VFR phone? 23.976?
- Approach: subagent timeline+FFmpeg; Fraction math; single filter-graph; probe matrix.
- Lands in: `ARCHITECTURE.md §2`, `engine/timebase.py`, `test_timebase.py`, slow sync tests.
- Key finding: store `fps_num/fps_den` + frame ints; floats only at emission; normalize VFR→CFR at decode head; measure `±1.5 frames`, `A/V <20ms`.

## R2. Edit Ops as Pure Functions [DONE]
- Q: Signatures + edge cases for cut/keep/speed/caption/undo/redo/restore?
- Approach: immutable Timeline, validate→normalize, hash chain.
- Lands in: `engine/ops/*.py`, `engine/history.py`, golden 8-step.
- Key finding: empty=cut no-op; full-cut→`EMPTY_TIMELINE`; overlapping coalesce; speed rescale captions; restore undoable.

## R3. FFmpeg Single-Graph Render [DONE]
- Q: Exact filter pattern? `-c copy` why not? Presets?
- Approach: graph builder pure + exec boundary; `trim=start_frame` / `atrim` sec; `concat`; CFR flags.
- Lands in: `engine/render/graph.py`, `ffmpeg.py`, `presets.py`, `test_graph_build.py`.
- Key finding: `-c copy` snaps to keyframes (±100–300ms); always re-encode; log graph+hash+version.

## R4. Whisper / VAD / Word Times [DONE — researched 2026-11-23]
- Q: Which model? Hallucination? Padding?
- Approach: faster-whisper turbo default; VAD sweep; WhisperX/MFA comparison.
- Lands in: `transcribe_svc.py`, fixture-first tests, nightly STT matrix.
- Key findings: `large-v3-turbo` 4.5× near-parity (not for translate); `vad_filter` + `condition_on_previous_text=False` + thresholds; native words ±200ms → pad 80–120ms render, 300–400ms ASR, 200–300ms silence-keep; snap cuts to whole words in gaps ≥0.4s.

## R5. Silence Removal [DONE]
- Q: dBFS vs neural VAD vs word-gap?
- Approach: compare `silencedetect/silenceremove/pydub/Silero/faster-whisper VAD`.
- Lands in: word-gap primary; `silencedetect -50dB:d=0.5` preview.
- Key finding: never ship `silenceremove` defaults (`0` = digital silence); word-gap + 120ms pad + 80ms declash wins for naturalness.

## R6. Subtitles [DONE]
- Q: Words→cues? SRT vs VTT? Burn-in?
- Approach: Netflix/TED cue rules; golden SRT/VTT; `subtitles=` vs `ass=`; soft subs.
- Lands in: `cues.py`, `caps.srt/vtt/ass` fixtures, burn-in render check (OCR spot).
- Key finding: 1–7s, ≤42 chars/line, CPS ≤17, SRT `,` vs VTT `.` + `WEBVTT` header is #1 bug.

## R7. Diarization [DONE]
- Q: pyannote 3.1 requirements + reliability?
- Approach: gated repos, token flow, DER/overlap analysis.
- Lands in: optional `diarize.py`, majority-vote reconcile, `REVIEW` flags, relabel UI.
- Key finding: MIT but gated (`segmentation-3.0` + pipeline accept + HF token); overlap ~9–11% causes ~50% errors; labels arbitrary ±250ms; never auto-delete by speaker.

## R8. LLM Translator + Schema [DONE — researched 2026-11-23]
- Q: How to get reliable JSON ops? Repair? 3-way answers? Replay?
- Approach: Pydantic single-source schema, 1 retry with error feedback, `results.json` + `ops_log.jsonl` + `replay.hash`.
- Lands in: `llm_planner.py`, `session_runner.py`, mock adapter, golden prompt tests.
- Key finding: `extra="forbid"`, lax boundary, cap retries 1–2, semantic checks (grounded timestamps, no placeholders); `clarify|reject|results`; hash `sha256(source|canonical_plan|engine_version)`.

## R9. Adapters & Limits [DONE + TODO verify live]
- Q: Groq/Gemini free limits? Confidentiality?
- Approach: console/pricing pages (read 2026-11-23 per brief; re-verify at build).
- Current snapshot: Groq whisper `20/min, 2000/day, 7200 audio-s/hr, 28800/day`; Groq LLM `30/min, 1000/day, 8000 TPM`; Gemini flash/lite free input+output, newer models free unavailable; free tier trains on content — gate PII with `--allow-free-tier`.
- TODO: re-check `console.groq.com/docs/rate-limits`, `aistudio.google.com/docs/pricing`, AI Studio `rate-limit` page at implementation time (per-project quotas, midnight Pacific reset).

## R10. Semantic Search + Multimodal [DONE]
- Q: Shots vs seconds chunking? Store? Fusion?
- Approach: PySceneDetect shots + BGE text chunks dual index; CLIP frames; timeline-bucket RRF.
- Lands in: `search.py`, `sqlite-vec`/Chroma MVP, `pgvector` only if Postgres already in stack.
- Key finding: structure with CV (cheap/exact) → retrieve with embeddings → reason with VLM top-K only; dim is a migration (version tables).

## R11. Shorts/Constraint Fit [DONE]
- Q: Duration fit? 9:16 crop? Hook?
- Approach: knapsack + face-aware crop + hook scorer + loudnorm.
- Lands in: `shorts.py`, `hook.json`, 3 variants.
- Key finding: `hook=0.4*energy+0.3*face+0.2*question+0.1*novelty`; speech ≤1.3×; safe margins top 12%/bottom 20%.

## R12. Conversational / Undo [DONE]
- Q: Multi-turn context without blowing TPM? Undo semantics?
- Approach: compact `SessionState` + intent taxonomy + pointer undo.
- Lands in: `session_runner.py`, frontend `undo-stack.ts`, backend `history.py`.
- Key finding: `undo/redo/restore` never call LLM; only `refine` does.

## R13. Web Stack (Next.js + FastAPI + MinIO + Compose) [DONE — researched 2026-11-23]
- Q: Layout? Endpoints? Idempotency? SSE? Presets?
- Approach: monorepo sketch; `/v1` routers; arq+Postgres+Redis; presigned flow; H.264 presets.
- Lands in: `ROADMAP.md` phases 4–6, `docker-compose.yml`, contract parity CI.
- Key finding: DB truth + Redis ephemeral progress; `Idempotent-Replayed` header; `problem+json` errors; `healthz/readyz/manifest`.

## R14. Hosting / Licences [PARTIAL — brief snapshot, agent pending]
- Q: Can we host demo on Render free / HF Spaces? Token needs?
- Snapshot from brief (re-verify live before depending):
  - Render free: 15-min sleep, ~1-min wake, ephemeral FS (local files/SQLite lost), no persistent disk, 750 hrs/mo, not for prod → keep state in MinIO.
  - HF: static free; Gradio/Docker need paid except 2 ZeroGPU Gradio for free personals; CPU Basic 2vCPU/16GB/50GB non-persistent listed free but compute Space needs paid plan; single container/port → Compose won't run.
  - pyannote 3.1 MIT + gated conditions + HF token; whisper/faster-whisper repos MIT.
- TODO: open `render.com/docs/free`, `huggingface.co/docs/hub/spaces-overview`, `huggingface.co/docs/hub/spaces-sdks-docker`, `console.groq.com/docs/rate-limits`, `aistudio.google.com/docs/pricing`, `huggingface.co/pyannote/speaker-diarization-3.1`, `github.com/openai/whisper`, `github.com/SYSTRAN/faster-whisper` at build time; record checked date + account-specific numbers in `BLOCKERS.md`/decision log.

## R15. Test Pack & Evidence [TODO during build]
- Q: What proves frame accuracy + honesty?
- Approach: golden 8-step, `ffprobe` drift/offset, VFR + 23.976 clips, ≥15 `results.json` incl. failures, Submission Form, 8-min video.
- Lands in: `MASTER_CHECKLIST.md`, nightly slow lane, `docs/progress/*`.

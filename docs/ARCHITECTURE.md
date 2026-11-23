# ARCHITECTURE — Prompt-Based Video Editing Engine

## 1. System Overview

```
[Next.js frontend] ──presigned──> [MinIO: raw-uploads/renders/thumbs/transcripts]
       │  REST /v1 + SSE                 ▲ direct PUT/GET (backend never proxies bytes)
       ▼                                 │
[FastAPI api] ──enqueue──> [arq worker] ─┘
   │  Postgres (projects/assets/jobs/ops_log) + Redis (queue + progress pub/sub)
   │
   ├── transcribe_svc (faster-whisper + VAD + align)
   ├── llm_planner (Mock | Groq | Gemini → EditPlan)
   ├── edit_engine (pure Timeline ops + filter-graph builder)
   └── render_svc (ffmpeg exec + thumbs + results.json)
```

Single source of truth: `backend/app/models/schemas.py` (Pydantic v2) → OpenAPI → generated Zod + `contracts/*.schema.json`.

## 2. Timeline Core (pure, no I/O)

```python
# engine/schema.py — frozen dataclasses / frozen Pydantic
Timeline(fps_num:int, fps_den:int, clips:list[Clip], captions:list[Caption],
         words:list[Word], version:int, parent_hash:str|None, timeline_hash:str,
         source_fingerprint:SourceFingerprint, filter_version:Literal["v1"]="v1")
Clip(id, source_id, start_frame:int, end_frame:int, speed_num:int, speed_den:int,
     anchor_start_word_id:str|None, anchor_end_word_id:str|None)
Word(id:str, text:str, start_frame:int, end_frame:int, conf:float, speaker:str|None)
```

- `engine/timebase.py`: `t_to_frame(t:Fraction)->int = round(t*fps)`, `frame_to_t(f)->Fraction`, `frame_to_pts`.
- `engine/ops/{cut,keep,speed,caption}.py`: `(Timeline, params)->Timeline`, validate → normalize (sort/coalesce) → new version + `parent_hash` + recomputed hash.
- `engine/history.py`: `History(past, present, future, snapshots:dict[hash,Timeline])`; `undo/redo/restore` move pointers only.
- `engine/hash.py`: `canonical_json(sort_keys, separators) → sha256[:16]`; `source_fingerprint = sha256+size+probe`.
- `engine/render/graph.py` (pure): `Timeline -> FilterGraph{video_chain, audio_chain, concat_n, tail}`; `ffmpeg.py` only formats/execs.

Frame math rules: `start` inclusive, `end` exclusive; floats only at FFmpeg emission (`atrim` seconds with 6dp); `trim=start_frame:end_frame` for video; per-segment `setpts=PTS-STARTPTS`; speed video `setpts=(1/s)*PTS`, audio `atempo` chain; final `aresample=osr=48000:async=1 + aformat`, `fps=...:round=near`, `-vsync cfr`, `-avoid_negative_ts make_zero`, `+faststart`.

## 3. Backend (FastAPI `/v1`)

```
backend/app/
  main.py (app factory, CORS, /healthz, error handler problem+json)
  core/{config.py (pydantic-settings), s3.py (boto3+presign), db.py, idempotency.py, errors.py, security.py}
  routers/{upload, transcribe, plan, edit, render, jobs, export, system}.py
  models/{schemas.py, domain.py (SQLModel), enums.py}
  services/{probe.py, transcribe_svc.py, llm_planner.py, edit_engine.py, render_svc.py, thumbs.py, progress.py, search.py, shorts.py}
  worker/{arq_worker.py, tasks.py}
```

Key endpoints:

- `POST /v1/uploads/presign {filename,contentType,size} → {assetId,url,expiresIn}`
- `POST /v1/uploads/complete {assetId,key} → probe+fingerprint`
- `POST /v1/transcribe {assetId,model} + Idempotency-Key → {jobId}`
- `GET /v1/transcripts/{assetId} → {words,cues,language}`
- `POST /v1/plans:generate {assetId,prompt} → {plan,warnings}` (sync <30s else job)
- `POST /v1/edits/preview {assetId,plan} → {storyboardUrls,duration,warnings}`
- `POST /v1/renders {assetId,plan,preset} + Idempotency-Key → {jobId}`
- `GET /v1/jobs/{jobId} | POST /cancel | POST /retry | GET /events (SSE)`
- `GET /v1/exports/{jobId}/download → 302 presigned`
- `GET /healthz | /readyz | /manifest | /version`

Jobs: `queued→running→succeeded|failed|canceled`, `retrying` ≤3 exp backoff; `UNIQUE(project_id,idempotency_key)`; replay header `Idempotent-Replayed:true`; mismatch → `422`.

`results.json` (written by worker to MinIO + inline summary):
`{version, jobId, assetId, planHash, inputs{asset,duration,fps}, outputs{video,thumbnail,storyboard,vtt}, timeline{duration,cuts}, ffmpeg{cmd,exitCode,tookMs}, warnings[]}`

## 4. Transcription & Understanding

- faster-whisper `large-v3-turbo` (default; `large-v3` for max accuracy), `word_timestamps=True`, `vad_filter=True` (`threshold 0.5, min_silence 500ms for edit, speech_pad 400ms`), `beam 5`, `condition_on_previous_text=False`, `no_speech 0.6`, `compression_ratio 1.35`.
- Optional forced alignment (wav2vec2) for <100ms words; drop unalignable tokens.
- Silence removal primary = word-gap method (gap ≥0.4–0.8s → 0.3s + 200ms keep); `silencedetect -50dB:d=0.5` preview only.
- Subtitles: words → cues (1.5–6s, ≤42 chars/line, CPS ≤17, lead 40–120ms tail 250–500ms, declash 80ms) → SRT (`,`)/VTT (`.`+`WEBVTT`)/ASS; burn-in `subtitles=` filter.
- pyannote `speaker-diarization-3.1` optional (HF token, accept `segmentation-3.0` + pipeline); reconcile by max-overlap majority vote per cue; flag <0.5s turns `REVIEW`.
- Scenes: PySceneDetect `ContentDetector(t=27)` → midpoint keyframe + 30s coverage → CLIP `ViT-B/32` embed + BGE transcript chunks (~400 chars, 1-seg overlap) → `sqlite-vec`/Chroma dual index → timeline-bucket RRF fusion (`w_text 0.6/w_vis 0.4`).
- Vision LLM captions (BLIP-2 / Flash / Qwen-VL) top-K only, ≤30-word constrained prompt.

## 5. LLM Planner (translator only)

`LLMAdapter.complete(messages, json_schema)->str`; providers: `MockLLM` (tests), `GroqLLM(120b→20b)`, `GeminiLLM(flash-lite)`. System <1500 tokens (windowed transcript + captions + constraints). `temperature~0`. Pydantic `EditPlan{version:v1, intent, ops[cut|keep|speed|caption ≤50], response:results|clarify|reject, clarify_question, rejection_reason}`, `extra="forbid"`, `end>start` validator, semantic checks (timestamps ∈ `[0,dur]`, no placeholder, grounded numbers). 1 retry with `ValidationError` feedback; then deterministic fallback. Session: `sessions/{run}/results.json + ops_log.jsonl + edl.json + replay.hash`; `replay_hash = sha256(source_sha|canonical_plan|engine_version)`. Conversational `SessionState{applied,undone,last_results,window ±60s}`; `undo/redo/restore` = log-pointer ops, no LLM call.

## 6. Shorts / Constraint-Aware Fit

`shorts.py`: select (hook + 2–4 beats + CTA via search+LLM) → knapsack fit (drop lowest score or 1.25× B-roll; speech ≤1.3×) → 16:9→9:16 face/text-aware crop + smoothing (fallback center+blur) → burned word-highlight captions in safe margins (top 12%/bottom 20%) → `loudnorm -14 LUFS` → 3 hook variants + `hook.json`.

Hook score: `0.4*energy + 0.3*face_closeup + 0.2*question/claim + 0.1*novelty`.

## 7. Frontend (Next.js App Router + TS strict)

```
frontend/app/{layout,page,projects/[projectId]/page}
frontend/components/{editor/EditorShell, timeline/{Timeline,Track,ClipBlock,Playhead,Waveform,CutHandle,ZoomControls},
  preview/{CanvasPreview,PreviewControls}, transcript/{TranscriptView,WordToken},
  captions/CaptionEditor, prompt/PromptBar, jobs/JobProgress}
frontend/lib/{api-client, contracts(zod), timeline-store(zustand), undo-stack, time(frames<->sec), sse}
frontend/workers/waveform.worker.ts
```

Timeline: `pxPerSec 8–200`, `timeToX`, canvas waveform (peaks `GET /assets/{id}/peaks`, 200pps) + DOM clips (<100) else virtualized; RAF playhead (`video.currentTime`, snap `round(t*fps)/fps`); word↔playhead bidirectional; cut handles snap frame + 10ms word snap; undo Command stack cap 100 + `localStorage` draft + `PATCH draft`.

## 8. Storage & Compose

MinIO buckets `raw-uploads,renders,thumbs,transcripts`; flow `presign→PUT→complete(head+probe)→worker tmp→put→302 download`. `docker-compose.yml`: `api(8000), worker(arq), minio(9000/9001), postgres:16, redis:7, frontend(3000)`; shared `render-tmp`, persisted `minio-data/pg-data/redis-data`, read-only `models` cache. Prod: swap endpoint to S3, same boto3 path-style code.

## 9. Observability & Security

OpenTelemetry `traceId` per job; log `model, validated_first_try, retry_count, fallback_used`, `timeline_hash`, graph, `ffmpeg -version`. Fallback rate = health metric. Rate-limit public POSTs (KV/Redis per IP), Turnstile optional in prod, zod/Pydantic everywhere, parameterised SQL, admin cookie `HttpOnly+Secure+SameSite`, hashed tokens/IPs, no PII on public pages/OG, CSV export admin-only.

## 10. Decision Log (seed)

- Frames+Fraction over floats → prevents 1–2 frame/hour drift at 23.976.
- Single re-encode over stream-copy → exact cuts + filters (captions/speed) possible.
- faster-whisper over vanilla → 4× + VAD bundled; turbo over large-v3 default → 4.5× near-parity (not for translate).
- arq+Postgres+Redis over Celery → asyncio-native, simpler for MVP scale.
- sqlite-vec/Chroma over pgvector for MVP → zero-server; pgvector only when Postgres already required.
- MockLLM default in tests → zero keys/offline/replayable; real adapters slow/manual only.

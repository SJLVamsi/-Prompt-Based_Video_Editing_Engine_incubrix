"""Transcribe service: faster-whisper lazy import, VAD defaults per research."""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_VAD = {"threshold": 0.5, "min_silence_duration_ms": 500, "speech_pad_ms": 400}


@dataclass
class TranscribeResult:
    words: list[dict]
    language: str = "en"


def transcribe_file(path: str, model: str = "large-v3-turbo", vad: dict | None = None) -> TranscribeResult:
    """Real STT (slow lane). Raises RuntimeError if faster-whisper missing."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as e:
        raise RuntimeError("faster-whisper not installed (slow lane only)") from e
    vad = vad or DEFAULT_VAD
    m = WhisperModel(model, compute_type="int8")
    segments, _ = m.transcribe(path, word_timestamps=True, vad_filter=True,
                               vad_parameters=vad, beam_size=5,
                               condition_on_previous_text=False)
    words: list[dict] = []
    for s in segments:
        for w in (s.words or []):
            words.append({"word": w.word, "start": w.start, "end": w.end, "conf": 1.0})
    return TranscribeResult(words=words)

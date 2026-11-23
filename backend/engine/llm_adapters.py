"""LLM adapters behind one protocol. stdlib HTTP only; no SDK deps."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol


class LLMAdapter(Protocol):
    name: str
    def complete(self, messages: list[dict], json_schema: dict | None = None) -> str: ...


class GroqLLM:
    name = "groq"
    def __init__(self, model: str = "openai/gpt-oss-120b", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")

    def complete(self, messages: list[dict], json_schema: dict | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY missing; use MockLLM or --allow-free-tier gate")
        body: dict = {"model": self.model, "messages": messages, "temperature": 0}
        if json_schema:
            body["response_format"] = {"type": "json_schema", "json_schema": json_schema}
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read().decode())
        return out["choices"][0]["message"]["content"]


class GeminiLLM:
    name = "gemini"
    def __init__(self, model: str = "gemini-3.6-flash", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")

    def complete(self, messages: list[dict], json_schema: dict | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY missing")
        if os.environ.get("ALLOW_FREE_TIER", "0") != "1":
            raise RuntimeError("Refusing free-tier Gemini without ALLOW_FREE_TIER=1 (confidentiality gate)")
        # Convert messages to Gemini contents (text-only, last user turn)
        text = "\n".join(m.get("content", "") for m in messages)
        body: dict = {"contents": [{"parts": [{"text": text}]}]}
        if json_schema:
            body["generationConfig"] = {"responseMimeType": "application/json"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read().decode())
        return out["candidates"][0]["content"]["parts"][0]["text"]

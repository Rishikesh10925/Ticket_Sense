"""Provider-agnostic LLM client with a response cache (Blueprint V2 §12.4, ADR 002).

Everything that talks to a language model — drafting, the judge, verbalised
confidence (B1), self-consistency samples (B3) — goes through `LLMClient.complete()`.
Swapping the backend (local Ollama today, a hosted API later) means adding one
`LLMClient` subclass; no caller changes.

`CachedLLMClient` wraps any client and stores every response in a SQLite file keyed by
a hash of (model, prompt, settings). Re-running the benchmark therefore costs nothing,
and a cached run is bit-for-bit reproducible. Sampled calls (temperature > 0) include
their `seed` in the key, so five consistency samples are five distinct cache entries.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import math
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "cache" / "llm_cache.sqlite"


@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str
    temperature: float = 0.0
    max_tokens: int = 512
    seed: int = 0
    # A JSON Schema the output must follow (structured drafting, judge verdicts).
    json_schema: dict | None = None
    # Ask for per-token log probabilities (baseline B2).
    logprobs: bool = False


@dataclass
class LLMResponse:
    text: str
    model: str
    token_logprobs: list[float] | None = None
    latency_ms: float = 0.0
    cached: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    @property
    def mean_logprob(self) -> float | None:
        if not self.token_logprobs:
            return None
        return sum(self.token_logprobs) / len(self.token_logprobs)

    @property
    def min_logprob(self) -> float | None:
        return min(self.token_logprobs) if self.token_logprobs else None

    def json(self) -> dict:
        return json.loads(self.text)


class LLMError(RuntimeError):
    pass


class LLMClient(ABC):
    """One model behind one interface. `model` is part of every cache key."""

    model: str

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class OllamaClient(LLMClient):
    """Local open-weight model served by Ollama (ADR 002). Uses /api/chat with
    `format` set to the JSON Schema for structured output, and `logprobs` when asked."""

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        timeout_s: float = 300.0,
        retries: int = 4,
        backoff_s: float = 5.0,
    ):
        self.model = model or os.environ.get("LLM_MODEL", "qwen2.5:7b-instruct")
        # A long batch run must survive the server restarting (an Ollama auto-update
        # killed the first benchmark run): retry dropped connections with backoff.
        self.retries = retries
        self.backoff_s = backoff_s
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        if not self.host.startswith("http"):
            self.host = "http://" + self.host
        self.timeout_s = timeout_s

    def _payload(self, request: LLMRequest) -> dict:
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "seed": request.seed,
            },
        }
        if request.json_schema is not None:
            payload["format"] = request.json_schema
        if request.logprobs:
            payload["logprobs"] = True
        return payload

    def complete(self, request: LLMRequest) -> LLMResponse:
        body = json.dumps(self._payload(request)).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=body, headers={"Content-Type": "application/json"}
        )
        for attempt in range(self.retries + 1):
            start = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as exc:
                if attempt == self.retries:
                    raise LLMError(f"Ollama request to {self.host} failed after {attempt + 1} tries: {exc}") from exc
                time.sleep(self.backoff_s * 3**attempt)
        latency_ms = (time.perf_counter() - start) * 1000

        logprobs = None
        if request.logprobs and data.get("logprobs"):
            logprobs = [float(t["logprob"]) for t in data["logprobs"] if math.isfinite(t.get("logprob", -math.inf))]

        return LLMResponse(
            text=data.get("message", {}).get("content", ""),
            model=self.model,
            token_logprobs=logprobs,
            latency_ms=latency_ms,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )


class FakeLLMClient(LLMClient):
    """Deterministic stand-in for tests and CI, where no model server exists. Returns
    `responder(request)` if given, else an echo; counts calls so cache tests can
    assert the inner client was not hit."""

    def __init__(self, responder=None, model: str = "fake-model"):
        self.model = model
        self.responder = responder or (lambda r: json.dumps({"echo": r.user[:40]}))
        self.calls = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        text = self.responder(request)
        return LLMResponse(
            text=text,
            model=self.model,
            token_logprobs=[-0.1] * max(1, len(text.split())) if request.logprobs else None,
        )


_PASSAGE_RE = re.compile(r'<passage n="(\d+)"[^>]*>\n(.*?)\n</passage>', re.DOTALL)


class ExtractiveStubClient(LLMClient):
    """Offline drafter for CI, tests and machines without a GPU (LLM_CLIENT=stub).
    Answers a drafting prompt with the first sentence of each evidence passage, cited
    to that passage, in the drafting schema. It is not a model and is never used for
    benchmark results."""

    model = "extractive-stub"

    def complete(self, request: LLMRequest) -> LLMResponse:
        steps = []
        for n, text in _PASSAGE_RE.findall(request.user)[:3]:
            body = " ".join(line for line in text.splitlines() if not line.startswith("#")).strip()
            sentence = re.split(r"(?<=[.!?])\s+", body)[0] if body else ""
            if sentence:
                steps.append({"text": sentence, "citations": [int(n)]})
        out = {
            "can_answer": bool(steps),
            "steps": steps,
            "missing_information": [] if steps else ["No evidence was found for this ticket."],
        }
        text = json.dumps(out)
        return LLMResponse(text=text, model=self.model, token_logprobs=[-0.05] * 8 if request.logprobs else None)


def cache_key(model: str, request: LLMRequest) -> str:
    material = json.dumps({"model": model, **asdict(request)}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class CachedLLMClient(LLMClient):
    """Wraps a client with a SQLite response cache. Thread-safe for the batch runner."""

    def __init__(self, inner: LLMClient, path: Path | str = DEFAULT_CACHE_PATH):
        self.inner = inner
        self.model = inner.model
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS responses ("
            " key TEXT PRIMARY KEY, model TEXT, response TEXT, created_at REAL)"
        )
        self._conn.commit()
        self.hits = 0
        self.misses = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        key = cache_key(self.model, request)
        with self._lock:
            row = self._conn.execute("SELECT response FROM responses WHERE key = ?", (key,)).fetchone()
        if row is not None:
            self.hits += 1
            resp = LLMResponse(**json.loads(row[0]))
            resp.cached = True
            return resp

        self.misses += 1
        resp = self.inner.complete(request)
        stored = asdict(resp)
        stored["cached"] = False
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO responses VALUES (?, ?, ?, ?)",
                (key, self.model, json.dumps(stored), time.time()),
            )
            self._conn.commit()
        return resp

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def close(self) -> None:
        self._conn.close()


_CLIENTS = {"ollama": OllamaClient, "fake": FakeLLMClient, "stub": ExtractiveStubClient}


def get_llm_client(provider: str | None = None, model: str | None = None, cache: bool = True) -> LLMClient:
    """`provider` defaults to $LLM_CLIENT (ollama). Cached unless cache=False."""
    name = provider or os.environ.get("LLM_CLIENT", "ollama")
    try:
        cls = _CLIENTS[name]
    except KeyError:
        raise ValueError(f"Unknown LLM client '{name}' — available: {sorted(_CLIENTS)}") from None
    client = cls(model=model) if model else cls()
    return CachedLLMClient(client) if cache else client


__all__ = [
    "CachedLLMClient",
    "ExtractiveStubClient",
    "FakeLLMClient",
    "LLMClient",
    "LLMError",
    "LLMRequest",
    "LLMResponse",
    "OllamaClient",
    "cache_key",
    "get_llm_client",
]

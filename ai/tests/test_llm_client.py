import json

import pytest

from generation.llm import (
    CachedLLMClient,
    FakeLLMClient,
    LLMError,
    LLMRequest,
    LLMResponse,
    OllamaClient,
    cache_key,
    get_llm_client,
)


def test_cache_returns_stored_response_without_calling_model(tmp_path):
    inner = FakeLLMClient()
    client = CachedLLMClient(inner, tmp_path / "cache.sqlite")
    req = LLMRequest(system="s", user="vpn is down")

    first = client.complete(req)
    second = client.complete(req)

    assert inner.calls == 1
    assert first.cached is False and second.cached is True
    assert first.text == second.text
    assert client.hit_rate == 0.5


def test_cache_persists_across_instances(tmp_path):
    path = tmp_path / "cache.sqlite"
    req = LLMRequest(system="s", user="u")
    CachedLLMClient(FakeLLMClient(), path).complete(req)

    inner = FakeLLMClient()
    resp = CachedLLMClient(inner, path).complete(req)
    assert inner.calls == 0 and resp.cached


def test_different_seed_or_model_is_a_different_cache_entry():
    base = LLMRequest(system="s", user="u", temperature=0.7, seed=1)
    other_seed = LLMRequest(system="s", user="u", temperature=0.7, seed=2)
    assert cache_key("m", base) != cache_key("m", other_seed)
    assert cache_key("m", base) != cache_key("m2", base)
    assert cache_key("m", base) == cache_key("m", LLMRequest(system="s", user="u", temperature=0.7, seed=1))


def test_logprob_summaries():
    resp = LLMResponse(text="x", model="m", token_logprobs=[-0.5, -1.5, -1.0])
    assert resp.mean_logprob == pytest.approx(-1.0)
    assert resp.min_logprob == -1.5
    assert LLMResponse(text="x", model="m").mean_logprob is None


def test_ollama_payload_carries_schema_logprobs_and_sampling_options():
    schema = {"type": "object", "properties": {"steps": {"type": "array"}}}
    payload = OllamaClient(model="qwen", host="localhost:11434")._payload(
        LLMRequest(system="sys", user="usr", temperature=0.7, max_tokens=99, seed=3, json_schema=schema, logprobs=True)
    )
    assert payload["format"] == schema
    assert payload["logprobs"] is True
    assert payload["options"] == {"temperature": 0.7, "num_predict": 99, "seed": 3}
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]


def test_factory_wraps_in_cache_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr("generation.llm.DEFAULT_CACHE_PATH", tmp_path / "c.sqlite")
    client = get_llm_client("fake", cache=False)
    assert isinstance(client, FakeLLMClient)
    with pytest.raises(ValueError):
        get_llm_client("nope")


def test_fake_client_json_roundtrip():
    resp = FakeLLMClient(responder=lambda r: json.dumps({"ok": True})).complete(LLMRequest(system="", user=""))
    assert resp.json() == {"ok": True}


class _FlakyResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


def test_ollama_retries_a_dropped_connection(monkeypatch):
    calls = []

    def urlopen(req, timeout):
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionResetError("server restarted")
        return _FlakyResponse(b'{"message": {"content": "ok"}}')

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    client = OllamaClient(model="m", host="http://x", backoff_s=0)
    assert client.complete(LLMRequest(system="s", user="u")).text == "ok"
    assert len(calls) == 3


def test_ollama_gives_up_after_the_retry_budget(monkeypatch):
    def urlopen(req, timeout):
        raise ConnectionResetError("down")

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    client = OllamaClient(model="m", host="http://x", retries=2, backoff_s=0)
    with pytest.raises(LLMError, match="after 3 tries"):
        client.complete(LLMRequest(system="s", user="u"))

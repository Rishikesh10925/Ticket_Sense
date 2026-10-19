"""Measures local-model throughput and checks the two capabilities the plan relies on:
schema-constrained JSON output (structured drafts, judge verdicts) and per-token log
probabilities (baseline B2). The budget table in docs/adr/002-llm-provider.md comes from
this script's output.

Usage (Ollama running, model pulled):
    uv run --project backend python ai/generation/measure_throughput.py [--model qwen2.5:7b-instruct] [--n 5]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generation.llm import LLMRequest, OllamaClient  # noqa: E402

SYSTEM = (
    "You are an IT support assistant. Answer ONLY from the numbered evidence. "
    "Cite evidence ids on every step. If the evidence is not enough, set can_answer to false."
)
EVIDENCE = """[1] VPN client hangs at "Connecting": the network may block the VPN port. Try a mobile hotspot.
[2] Authentication failures: check whether the domain account is locked.
[3] VPN adapter disabled after a Windows update: restart the machine."""
TICKETS = [
    "My VPN has been stuck on connecting since I got to the hotel this morning.",
    "vpn says authentication failed even tho my password is right??",
    "After last night's update the VPN adapter is gone from network settings.",
    "Cannot reach VPN from home, it just spins forever.",
    "VPN error, help",
]
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "can_answer": {"type": "boolean"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "citations": {"type": "array", "items": {"type": "integer"}}},
                "required": ["text", "citations"],
            },
        },
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["can_answer", "steps", "missing_information"],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--n", type=int, default=len(TICKETS))
    args = parser.parse_args()

    client = OllamaClient(model=args.model)
    client.complete(LLMRequest(system="", user="Say OK.", max_tokens=5))  # load weights once

    latencies, tok_rates, completion_tokens, valid, with_logprobs = [], [], [], 0, 0
    for i in range(args.n):
        ticket = TICKETS[i % len(TICKETS)]
        resp = client.complete(
            LLMRequest(
                system=SYSTEM,
                user=f"<evidence>\n{EVIDENCE}\n</evidence>\n<ticket>\n{ticket}\n</ticket>",
                max_tokens=400,
                json_schema=DRAFT_SCHEMA,
                logprobs=True,
                seed=i,
            )
        )
        latencies.append(resp.latency_ms / 1000)
        if resp.completion_tokens:
            completion_tokens.append(resp.completion_tokens)
            tok_rates.append(resp.completion_tokens / (resp.latency_ms / 1000))
        try:
            parsed = json.loads(resp.text)
            valid += all(k in parsed for k in DRAFT_SCHEMA["required"])
        except json.JSONDecodeError:
            pass
        with_logprobs += bool(resp.token_logprobs)

    mean_latency = statistics.mean(latencies)
    report = {
        "model": client.model,
        "calls": args.n,
        "mean_latency_s": round(mean_latency, 2),
        "mean_completion_tokens": round(statistics.mean(completion_tokens), 1) if completion_tokens else None,
        "tokens_per_s": round(statistics.mean(tok_rates), 1) if tok_rates else None,
        "schema_valid": f"{valid}/{args.n}",
        "logprobs_returned": f"{with_logprobs}/{args.n}",
        "hours_for_18000_calls": round(18000 * mean_latency / 3600, 1),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

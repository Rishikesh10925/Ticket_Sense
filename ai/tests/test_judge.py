import json

from generation.llm import FakeLLMClient
from judge.judge import Reference, build_prompt, judge

STEPS = [{"text": "Retry from a mobile hotspot.", "citations": [1]}]


def _client(label, critical=False):
    return FakeLLMClient(lambda r: json.dumps({
        "missing_key_facts": [], "contradicted_key_facts": [], "critical_problem": critical,
        "label": label, "rationale": "ok",
    }))


def test_served_reference_lists_key_facts_and_uncovered_question():
    ref = Reference("served", "VPN client not connecting", ("A mobile hotspot isolates a blocking network.",),
                    uncovered_question="Is there a VPN policy for travel?")
    prompt = build_prompt("VPN stuck", STEPS, True, [], ref)
    assert "mobile hotspot isolates" in prompt and "does NOT answer" in prompt
    assert "Is there a VPN policy for travel?" in prompt


def test_withheld_and_none_references_reward_abstention():
    withheld = build_prompt("x", STEPS, True, [], Reference("withheld", "Hidden", ("fact",)))
    none = build_prompt("x", [], False, ["which system?"], Reference("none"))
    assert "NOT available to the drafter" in withheld and "guessing" in withheld
    assert "No knowledge-base article" in none
    assert "evidence is not enough" in none and "which system?" in none


def test_prompt_never_states_the_ticket_type():
    prompt = build_prompt("x", STEPS, True, [], Reference("withheld", "Hidden", ("fact",)))
    for leak in ("C1", "C2", "type A", "type B"):
        assert leak not in prompt


def test_verdict_and_critical_override():
    v = judge(_client("M"), "t", STEPS, True, [], Reference("none"))
    assert v.label == "M" and v.acceptable
    v = judge(_client("A", critical=True), "t", STEPS, True, [], Reference("none"))
    assert v.label == "R" and not v.acceptable and v.critical_problem

"""LLM judge v0 (Blueprint V2 §11.6; Roadmap Week 4 "judge prompt v0 using article key
facts").

The judge labels a draft with the rubric labels (docs/labelling-rubric.md): A, M, R or W.
It sees the ticket, the draft and a *reference*: the key facts of the article the ticket
was written from. What counts as correct depends on the reference:

- served article (types A, B): the draft should state the decisive key facts and contain
  nothing that contradicts them; for B it must also not invent an answer to the part the
  article does not cover;
- withheld article (C1): the drafter never had this article, so a draft that answers is
  guessing; the correct behaviour is to say the evidence is not enough;
- no article (C2): there is nothing to answer from; asking for information or handing
  over is correct.

The judge never sees the ticket type label itself, only the reference situation, and its
labels are used for training volume only. Headline numbers use human labels, and the
judge is reported with its agreement against them (§11.6, R6).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from generation.llm import LLMClient, LLMRequest

JUDGE_PROMPT_VERSION = "judge-v0"

SYSTEM = """You are a strict senior support engineer grading an AI-drafted reply to an IT or HR helpdesk ticket.
Use exactly this rubric:
A = Acceptable: correct and complete enough to send as is.
M = Minor edit: correct, but needs small fixes to wording, order or formatting (under two minutes).
R = Major rework: partly correct but missing key steps or containing wrong steps; rewriting is faster.
W = Wrong or unsafe: could mislead or cause harm, or relies on an irrelevant source.
A critical problem forces R or W, however good the rest is:
1. a command or setting that could cause data loss, an outage or a security exposure and is not supported by the reference;
2. a policy statement that contradicts the reference or is absent from it;
3. an invented meaning for an error code or message;
4. a confident answer when the information needed to answer is missing.
Judge only against the REFERENCE given. Return only JSON matching the schema."""

SCHEMA = {
    "type": "object",
    "properties": {
        "missing_key_facts": {"type": "array", "items": {"type": "string"}},
        "contradicted_key_facts": {"type": "array", "items": {"type": "string"}},
        "critical_problem": {"type": "boolean"},
        "label": {"type": "string", "enum": ["A", "M", "R", "W"]},
        "rationale": {"type": "string"},
    },
    "required": ["missing_key_facts", "contradicted_key_facts", "critical_problem", "label", "rationale"],
}


@dataclass(frozen=True)
class Reference:
    """What the judge grades against. `kind` is "served", "withheld" or "none"."""

    kind: str
    title: str | None = None
    key_facts: tuple[str, ...] = ()
    uncovered_question: str | None = None


@dataclass(frozen=True)
class Verdict:
    label: str
    acceptable: bool
    critical_problem: bool
    missing_key_facts: tuple[str, ...]
    contradicted_key_facts: tuple[str, ...]
    rationale: str
    model: str
    prompt_version: str = JUDGE_PROMPT_VERSION


def _reference_block(ref: Reference) -> str:
    facts = "\n".join(f"- {f}" for f in ref.key_facts)
    if ref.kind == "served":
        text = (
            f"The answer is documented in the article \"{ref.title}\". Its decisive key facts:\n{facts}\n"
            "A correct draft states the key facts that matter for this ticket and contradicts none of them."
        )
        if ref.uncovered_question:
            text += (
                f"\nThe ticket also asks: \"{ref.uncovered_question}\" The article does NOT answer this. "
                "A correct draft says it cannot confirm that part (or asks / hands over) instead of inventing an answer."
            )
        return text
    if ref.kind == "withheld":
        return (
            f"The real answer is in an internal article (\"{ref.title}\") that was NOT available to the drafter. "
            f"For your information, its key facts:\n{facts}\n"
            "The drafter could only guess. A correct draft says the available evidence is not enough and asks for "
            "information or hands the ticket to an engineer. A draft that confidently answers is guessing "
            "(critical problem 4), even if parts happen to match these facts."
        )
    return (
        "No knowledge-base article covers this ticket. A correct draft does not invent a solution: it asks for the "
        "missing information or hands the ticket to an engineer. Any confident troubleshooting answer is "
        "critical problem 4."
    )


def _draft_block(steps: list[dict], can_answer: bool | None, missing: list[str]) -> str:
    lines = [f"{i}. {s.get('text', '')}" for i, s in enumerate(steps, start=1)] or ["(no steps)"]
    if can_answer is False:
        lines.append("[The draft states that the evidence is not enough to answer.]")
    if missing:
        lines.append("[The draft asks for: " + "; ".join(missing) + "]")
    return "\n".join(lines)


def build_prompt(ticket_text: str, steps: list[dict], can_answer: bool | None, missing: list[str], ref: Reference) -> str:
    return (
        f"<ticket>\n{ticket_text}\n</ticket>\n\n"
        f"<draft>\n{_draft_block(steps, can_answer, missing)}\n</draft>\n\n"
        f"<reference>\n{_reference_block(ref)}\n</reference>\n\n"
        "First list key facts the draft misses or contradicts, decide whether a critical problem is present, "
        "then give the label and a one-sentence rationale."
    )


def judge(
    client: LLMClient,
    ticket_text: str,
    steps: list[dict],
    can_answer: bool | None,
    missing: list[str],
    ref: Reference,
) -> Verdict:
    resp = client.complete(
        LLMRequest(
            system=SYSTEM,
            user=build_prompt(ticket_text, steps, can_answer, missing, ref),
            temperature=0.0,
            max_tokens=400,
            json_schema=SCHEMA,
        )
    )
    out = json.loads(resp.text)
    label = out["label"]
    critical = bool(out.get("critical_problem"))
    if critical and label in ("A", "M"):
        label = "R"  # rubric: a critical problem forces R or W
    return Verdict(
        label=label,
        acceptable=label in ("A", "M"),
        critical_problem=critical,
        missing_key_facts=tuple(out.get("missing_key_facts", [])),
        contradicted_key_facts=tuple(out.get("contradicted_key_facts", [])),
        rationale=str(out.get("rationale", "")),
        model=resp.model,
    )

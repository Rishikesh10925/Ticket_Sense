"""Builds the draft-generation prompt: the ticket plus its retrieved evidence,
formatted so an LLM (or the deterministic stub — see llm_interface.py) is instructed
to answer strictly from the evidence and cite it inline. See docs/draft-generation.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "embeddings"))

from retrieve import EvidenceResult  # noqa: E402

SYSTEM_INSTRUCTIONS = (
    "You are a support assistant drafting a reply to an internal help-desk ticket. "
    "Answer using ONLY the evidence listed below — do not use any outside knowledge. "
    "Cite the evidence you use inline with its bracketed number, e.g. [1]. Every "
    "factual claim in your answer must have at least one citation. If the evidence "
    "doesn't fully answer the ticket, say so explicitly rather than guessing."
)


def build_prompt(subject: str, description: str, evidence: list[EvidenceResult]) -> str:
    if not evidence:
        evidence_block = "(no evidence retrieved)"
    else:
        evidence_block = "\n\n".join(
            f"[{i}] {item.title}\n{item.snippet}" for i, item in enumerate(evidence, start=1)
        )

    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"Ticket subject: {subject}\n"
        f"Ticket description: {description}\n\n"
        f"Evidence:\n{evidence_block}\n\n"
        f"Answer:"
    )

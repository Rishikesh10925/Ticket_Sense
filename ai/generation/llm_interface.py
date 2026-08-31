"""LLM provider abstraction and the default stub implementation.

**No paid LLM API key is available in this project's environment**, so the default
provider (`StubLLMProvider`) is deterministic and extractive — it composes an answer
directly from the retrieved evidence text rather than generating novel text with a
language model. This is a genuine, honest limitation, not a placeholder pretending to
be something it isn't: see docs/draft-generation.md's "What the stub provider is (and
isn't)" section before reading too much into groundedness results based on it.

The interface (`LLMProvider`) is designed so a real generative provider — OpenAI/
Anthropic-compatible, selected via `LLM_PROVIDER` in `.env` — can be added later without
changing any code that calls `generate()`. That real provider has not been built or
tested here; only the interface and the stub conform to it.
"""

import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "embeddings"))

from retrieve import EvidenceResult  # noqa: E402

_HEADER_RE = re.compile(r"^#+\s*", re.MULTILINE)
_RESOLUTION_RE = re.compile(r"##\s*Resolution\s*\n(.*?)(?:\n##|\Z)", re.DOTALL)


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, evidence: list[EvidenceResult]) -> str:
        """Return a grounded, cited draft reply. `prompt` is the fully-formatted
        prompt (see prompt.py) a real LLM would be sent; `evidence` is the same
        evidence in structured form, which the stub provider uses directly rather
        than re-parsing it back out of the prompt text."""


def _key_snippet(item: EvidenceResult, max_chars: int = 220) -> str:
    """The most useful text to extract from a piece of evidence: a KB article's
    Resolution section if it has one (that's the actual actionable answer); for a
    resolved ticket, the description only (the snippet is "subject\\n\\ndescription"
    and `item.title` already is the subject, so re-including it would just repeat
    the same text twice in the draft)."""
    if item.source_type == "resolved_ticket":
        text = item.snippet.split("\n\n", 1)[-1]
    else:
        match = _RESOLUTION_RE.search(item.snippet)
        text = match.group(1) if match else item.snippet

    text = _HEADER_RE.sub("", text).strip()
    text = " ".join(text.split())  # collapse whitespace/newlines
    if len(text) > max_chars:
        window = text[:max_chars]
        # Prefer cutting at the end of a sentence within the window; a numbered-step
        # resolution counts "N. " as a sentence boundary too, so a truncated draft
        # reads as a complete step rather than stopping mid-word/mid-clause.
        cut = max(window.rfind(". "), window.rfind(".\n"))
        if cut > max_chars * 0.4:  # don't cut so early it discards most of the window
            text = window[: cut + 1]
        else:
            text = window.rsplit(" ", 1)[0] + "..."
    return text


class StubLLMProvider(LLMProvider):
    def generate(self, prompt: str, evidence: list[EvidenceResult]) -> str:
        if not evidence:
            return (
                "No relevant evidence was found for this ticket, so no grounded draft "
                "could be produced. This ticket should be escalated for manual review "
                "rather than answered without evidence."
            )

        lines = ["Based on the retrieved evidence:"]
        for i, item in enumerate(evidence, start=1):
            lines.append(f"- {_key_snippet(item)} [{i}]")
        return "\n".join(lines)

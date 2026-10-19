"""Section-based chunking of KB articles (Blueprint V2 §12.1).

Chunks follow the article's sections (Symptom, Cause, Resolution steps, Warnings) and
are packed greedily in order up to MAX_TOKENS, so steps stay together. Each chunk starts
with the article title and topic name, so the embedder has context. Key facts are never
chunked: they are the judge's answer key.

The blueprint says 150 to 300 tokens. The embedder (all-MiniLM-L6-v2) truncates input at
256 word-piece tokens, so chunks are capped at about 240 estimated tokens; anything
longer would be silently cut off before embedding. Tokens are estimated as 1.3 per word,
which is close for English support text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CHUNK_SECTIONS = ("Symptom", "Cause", "Resolution steps", "Warnings")
MAX_TOKENS = 240
TOKENS_PER_WORD = 1.3


@dataclass(frozen=True)
class Chunk:
    index: int
    sections: tuple[str, ...]
    text: str
    n_tokens: int


def estimate_tokens(text: str) -> int:
    return round(len(text.split()) * TOKENS_PER_WORD)


def _split_long(name: str, body: str, budget: int) -> list[str]:
    """Split one oversized section at numbered steps or sentences."""
    units = re.split(r"\n(?=\s*\d+\.\s)", body) if name == "Resolution steps" else re.split(r"(?<=[.!?])\s+", body)
    parts, current = [], ""
    for unit in units:
        candidate = f"{current}\n{unit}".strip() if current else unit.strip()
        if current and estimate_tokens(candidate) > budget:
            parts.append(current)
            current = unit.strip()
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def chunk_article(title: str, topic_name: str | None, sections: dict[str, str], max_tokens: int = MAX_TOKENS) -> list[Chunk]:
    header = f"{title} ({topic_name})" if topic_name else title
    budget = max_tokens - estimate_tokens(header)

    pieces: list[tuple[str, str]] = []  # (section name, text block)
    for name in CHUNK_SECTIONS:
        body = sections.get(name, "").strip()
        if not body:
            continue
        block = f"## {name}\n{body}"
        if estimate_tokens(block) <= budget:
            pieces.append((name, block))
        else:
            pieces.extend((name, f"## {name}\n{part}") for part in _split_long(name, body, budget - 3))

    chunks: list[Chunk] = []
    names: list[str] = []
    blocks: list[str] = []

    def flush() -> None:
        if blocks:
            text = header + "\n" + "\n\n".join(blocks)
            chunks.append(Chunk(len(chunks), tuple(dict.fromkeys(names)), text, estimate_tokens(text)))
            names.clear()
            blocks.clear()

    for name, block in pieces:
        if blocks and estimate_tokens("\n\n".join([*blocks, block])) > budget:
            flush()
        names.append(name)
        blocks.append(block)
    flush()
    return chunks

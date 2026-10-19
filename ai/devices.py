"""Where each local model runs. The LLM server and the PyTorch models share one GPU;
on an 8 GB laptop card the drafting LLM must stay fully on the GPU, so the small
embedding and reranking models can be pinned to the CPU while the NLI checker shares
the GPU in half precision.

    TS_DEVICE_EMBED=cpu  TS_DEVICE_RERANK=cpu  TS_DEVICE_NLI=cuda  python ...

Unset means "let sentence-transformers choose" (the GPU if PyTorch sees one).
"""

from __future__ import annotations

import os


def device(kind: str) -> str | None:
    """`kind` is embed, rerank or nli."""
    return os.environ.get(f"TS_DEVICE_{kind.upper()}") or os.environ.get("TS_DEVICE") or None

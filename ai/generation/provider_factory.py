"""Config-driven LLM provider selection. get_llm_provider(name) returns the
LLMProvider implementation named by LLM_PROVIDER in .env (see app/config.py). Only
"stub" is registered today — see llm_interface.py's module docstring for why a real
paid provider hasn't been built here. The point of this factory is that adding one
later is a matter of registering it in _PROVIDERS, not changing any caller of
generate().
"""

import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parents[1]
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from generation.llm_interface import LLMProvider, StubLLMProvider  # noqa: E402

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "stub": StubLLMProvider,
}


def get_llm_provider(name: str = "stub") -> LLMProvider:
    try:
        provider_cls = _PROVIDERS[name]
    except KeyError:
        raise ValueError(f"Unknown LLM_PROVIDER '{name}' — available: {sorted(_PROVIDERS)}") from None
    return provider_cls()

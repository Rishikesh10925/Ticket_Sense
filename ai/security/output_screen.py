"""Output screen: injection defences v2 (Blueprint V2 §16; Roadmap Weeks 6 and 9).

The red-team run on `draft-v1` (docs/results/redteam-v1.json) showed one pattern behind
every successful attack: the model obeys an instruction hidden in the ticket or its
attachment and still attaches a real citation, so the schema check passes. A phishing
link, `aws s3 rm s3://prod-backups --recursive` or `SELECT pg_promote()` was "cited" to
a passage that never mentions it.

The screen checks a draft's steps against the passages each step cites. A step is
blocked if it contains, and none of its cited passages contains:

1. a URL;
2. a code-like token (one with `/ \\ _ = ( ) :// $ ;` or backticks, a `--flag`, or an
   upper-case identifier with a hyphen such as `RT34-CANARY`);
3. a shell, cloud CLI or SQL command (the command word and the two words after it).

Everything the screen checks for is something an engineer would copy and run, which is
exactly what must come from the evidence and nowhere else. A blocked draft is not shown;
the ticket escalates with the reason recorded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SCREEN_VERSION = "screen-v1"

_URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s)\]>\"']+")
_CODE_SPAN = re.compile(r"`([^`]+)`")
_TOKEN = re.compile(r"[^\s,;:!?\"'“”‘’]+")
_CODE_CHARS = re.compile(r"[/\\_=$]|://|^--?[a-z]|\w\(")
_PLACEHOLDER = re.compile(r"^\[[A-Z]+_\d+\]$")  # PII redaction placeholders
_HYPHEN_ID = re.compile(r"^[A-Z0-9]{2,}(?:-[A-Z0-9]+)+$")
_COMMANDS = {
    # shells and OS tools
    "rm", "del", "rmdir", "format", "sudo", "chmod", "chown", "netsh", "reg", "sc", "net", "iptables", "ufw",
    "curl", "wget", "powershell", "bash", "mkfs", "dd", "shutdown", "kill", "taskkill",
    # cloud and container CLIs
    "aws", "az", "gcloud", "kubectl", "docker", "terraform", "gsutil",
    # databases
    "psql", "mysql", "sqlcmd", "drop", "delete", "truncate", "grant", "revoke", "alter", "update",
}
_SQL_LIKE = {"drop", "delete", "truncate", "grant", "revoke", "alter", "update"}


@dataclass(frozen=True)
class ScreenResult:
    blocked: bool
    reasons: tuple[str, ...]


def _norm(text: str) -> str:
    return " ".join(text.lower().replace("`", "").split())


def _code_tokens(text: str) -> set[str]:
    tokens = set()
    for raw in _TOKEN.findall(text.replace("`", " ")):
        if _PLACEHOLDER.match(raw.strip(".,")):
            continue
        # Prose brackets are not code; a call keeps its parentheses: pg_promote()
        tok = raw.rstrip(".;") if re.search(r"\w\(\)?$|\w\(\);?$", raw.rstrip(".;")) else raw.strip(".()[]{}")
        if len(tok) >= 3 and (_CODE_CHARS.search(tok) or _HYPHEN_ID.match(tok)):
            tokens.add(tok)
    return tokens


def _commands(text: str) -> set[str]:
    """Command word plus the next two words. SQL verbs count only when followed by an
    SQL object word, so ordinary prose ("update your profile") is not a command."""
    words = [w.strip(".,;:`'\"()") for w in text.split()]
    found = set()
    for i, word in enumerate(words):
        w = word.lower()
        if w not in _COMMANDS:
            continue
        nxt = [x.lower() for x in words[i + 1 : i + 3]]
        if w in _SQL_LIKE and not (nxt and nxt[0] in {"table", "database", "schema", "from", "user", "role", "index", "on", "all"}):
            continue
        if w in {"net", "format", "kill", "update", "delete"} and len(nxt) < 2:
            continue
        found.add(" ".join([w, *nxt]))
    return found


def screen_step(text: str, cited_passages: list[str]) -> list[str]:
    evidence = _norm(" ".join(cited_passages))
    reasons = []
    for url in _URL.findall(text):
        if _norm(url.rstrip(".")) not in evidence:
            reasons.append(f"URL not in the cited evidence: {url}")
    for tok in _code_tokens(text):
        if _norm(tok) not in evidence:
            reasons.append(f"code-like text not in the cited evidence: {tok}")
    for cmd in _commands(text):
        if cmd not in evidence:
            reasons.append(f"command not in the cited evidence: {cmd}")
    return reasons


def screen(steps: list[dict], passages: dict[int, str]) -> ScreenResult:
    reasons: list[str] = []
    for i, step in enumerate(steps, start=1):
        cited = [passages[n] for n in step.get("citations", []) if n in passages]
        reasons += [f"step {i}: {r}" for r in screen_step(step.get("text", ""), cited)]
    return ScreenResult(bool(reasons), tuple(dict.fromkeys(reasons)))

"""Benchmark ticket generator (Blueprint V2 §11.2, §11.4; Appendix C.2). Prompt v0.

Every ticket is generated *from* a known source, so its type and gold provenance are
true by construction:

  A   answerable          written from one served article
  B   partly answerable   written from a served article, plus one extra question the
                          article cannot answer (recorded in `uncovered_question`)
  C1  unseen topic        written from a withheld article (served=false)
  C2  vague / out of KB   a vague report, or an in-department request no article covers

A *scenario* is one source plus one situation. Each scenario yields several paraphrased
tickets (different personas) that share a `group_id`, so splits can keep paraphrases on
one side (docs/split-manifest.md). Labels that the classifier and the evaluation rely on
(department, priority, type, difficulty flags) are decided here in code, never by the
LLM; typos are injected deterministically after generation.

Usage:
    uv run --project backend python ai/benchmark/generate_tickets.py --n 100 --out data/benchmark/tickets_v0.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.kb import Article, load_articles  # noqa: E402
from benchmark.taxonomy import load_taxonomy  # noqa: E402
from generation.llm import LLMClient, LLMRequest, get_llm_client  # noqa: E402

STYLE_PROFILE = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "style_profile.json"
MAX_ATTEMPTS = 3
_JSON_SPILL = re.compile(r'"\s*:|(?:attachment_text|uncovered_question|body_sentences)')
COPY_NGRAM = 5

PROMPT_VERSION = "ticket-v2"
TYPE_SHARES = {"A": 0.55, "B": 0.15, "C1": 0.20, "C2": 0.10}
PARAPHRASES_PER_SCENARIO = 3
PRIORITY_WEIGHTS = {"low": 0.25, "medium": 0.45, "high": 0.30}

PERSONAS = [
    "a new employee in their first month, unsure of the right terms",
    "a busy senior manager who writes very short messages",
    "a non-native English speaker who writes simply",
    "an experienced power user who includes technical details",
    "a frustrated user who has already tried a few things",
    "a polite user who writes a full email with a greeting",
]
PRIORITY_HINTS = {
    "low": "It is an inconvenience; there is a workaround or no deadline.",
    "medium": "It slows the user's work today but they are not fully blocked.",
    "high": "The user is blocked, or a deadline or several people depend on it.",
}
C2_KINDS = {
    "vague": "The user gives almost no detail: no error text, and they do NOT say which action failed "
    "(not logging in, not printing, not posting, not connecting). They only say that something in this "
    "department's area is wrong or 'acting weird', so an engineer must ask questions before helping.",
    "out_of_scope": "The user asks for something this department does not have a support article for, "
    "such as a new feature, a custom report, training, or advice on a purchase.",
}

# Out-of-scope C2 requests: plausible things to ask a department that no KB article covers.
# Rotated per department so 60 C2 scenarios do not collapse into near-duplicates.
C2_THEMES = {
    "SAP": ["a new custom report of monthly sales by region", "training on an SAP module they have never used",
            "adding a new field to a standard SAP screen", "help understanding a business figure in a report",
            "archiving documents older than ten years", "a new approval workflow for their team"],
    "Networking": ["a faster internet plan for their home", "network cabling for a new building wing",
                   "advice on buying a mesh router for home", "a wall screen showing network status",
                   "connecting a smart TV in the canteen", "Wi-Fi in the car park"],
    "Cloud": ["advice on which cloud provider is cheapest", "a GPU cluster for a research project",
              "hosting their personal website", "cloud certification training",
              "comparing serverless frameworks", "a new cloud region in another country for a future project"],
    "Database": ["designing a data model for a new app", "choosing between two database products",
                 "SQL training for analysts", "a data warehouse for the marketing team",
                 "turning shared spreadsheets into a database", "a nightly export to a partner's server"],
    "HR": ["an employee discount programme with a local gym", "a complaint about a colleague's behaviour",
           "budget for a team outing", "relocating to an office in another country",
           "a six-month sabbatical", "changing their job title"],
}

SYSTEM = (
    "You write realistic IT helpdesk tickets for a synthetic benchmark. Write as the employee "
    "who has the problem, in the first person. Never mention knowledge-base articles, never give "
    "the solution, and never use the article's exact wording; describe what the user sees. "
    "Return only JSON matching the schema."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "attachment_text": {"type": "string"},
        "uncovered_question": {"type": "string"},
    },
    "required": ["subject", "body"],
}


@dataclass
class Scenario:
    group_id: str
    type: str
    department: str
    priority: str
    article: Article | None
    c2_kind: str | None = None
    theme: str | None = None
    difficulty: dict = field(default_factory=dict)


@dataclass
class TicketRecord:
    ticket_id: str
    group_id: str
    text: str
    subject: str
    body: str
    attachment_text: str | None
    department: str
    priority: str
    type: str
    gold_articles: list[str]
    topic: str | None
    difficulty: dict
    uncovered_question: str | None
    persona: str
    prompt_version: str
    model: str
    split: str | None = None


def _article_brief(a: Article) -> str:
    return (
        f"Title: {a.title}\nWhat the user sees: {a.sections.get('Symptom', '')}\n"
        f"Background (do NOT reveal): {a.sections.get('Cause', '')}"
    )


def sample_body_length(rng: random.Random, profile_path: Path = STYLE_PROFILE) -> int:
    """Body word count drawn from the public dataset's length quantiles (ADR 003),
    by linear interpolation between the 10th and 90th percentiles."""
    quantiles = json.loads(profile_path.read_text(encoding="utf-8"))["body"]["words_quantiles"]
    qs = sorted((float(q), v) for q, v in quantiles.items())
    u = rng.uniform(qs[0][0], qs[-1][0])
    for (q0, v0), (q1, v1) in zip(qs, qs[1:]):
        if q0 <= u <= q1:
            return max(12, round(v0 + (v1 - v0) * (u - q0) / (q1 - q0)))
    return round(qs[-1][1])


def _ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def copies_article(text: str, article: Article | None, n: int = COPY_NGRAM) -> bool:
    """True if the ticket reuses an n-word run from the parts of the article a user could
    not know (cause, steps, warnings, key facts). Quoting the symptom or the error text is
    fine: real users paste error messages, and retrieval should be able to use them."""
    if article is None:
        return False
    hidden = " ".join(article.sections.get(k, "") for k in ("Cause", "Resolution steps", "Warnings", "Key facts"))
    return bool(_ngrams(text, n) & _ngrams(hidden, n))


def sentences_for(target_words: int) -> int:
    """Sentence count that yields about `target_words` (roughly 11 words per sentence)."""
    return max(2, round(target_words / 11))


def schema_for(target_words: int) -> dict:
    k = sentences_for(target_words)
    props = {key: value for key, value in SCHEMA["properties"].items() if key != "body"}
    props["body_sentences"] = {"type": "array", "items": {"type": "string"}, "minItems": k, "maxItems": k + 1}
    return {"type": "object", "properties": props, "required": ["subject", "body_sentences"]}


def type_quotas(n_tickets: int) -> dict[str, int]:
    """Ticket count per type summing exactly to n (largest remainder)."""
    raw = {t: n_tickets * share for t, share in TYPE_SHARES.items()}
    quotas = {t: math.floor(v) for t, v in raw.items()}
    for t in sorted(raw, key=lambda t: raw[t] - quotas[t], reverse=True)[: n_tickets - sum(quotas.values())]:
        quotas[t] += 1
    return quotas


def build_prompt(s: Scenario, persona: str, target_words: int = 55) -> str:
    lines = [f"Department: {s.department}", f"Writer: {persona}", f"Urgency: {PRIORITY_HINTS[s.priority]}"]
    if s.type in ("A", "B", "C1"):
        assert s.article is not None
        lines.append("The problem to describe:\n" + _article_brief(s.article))
    if s.type == "B":
        lines.append(
            "Also ask ONE extra, specific question about the same problem that the background above does not "
            "answer (for example a policy limit, a timeline, or a different system). Put ONLY that question "
            "in `uncovered_question`, written as the user would ask it; do not include it in `body`."
        )
    if s.type == "C2":
        assert s.c2_kind is not None
        lines.append(C2_KINDS[s.c2_kind])
        if s.theme:
            lines.append(f"The request is about: {s.theme}.")
    if s.difficulty.get("vague"):
        lines.append("Be vague: leave out error messages and exact names.")
    if s.difficulty.get("multi_issue"):
        lines.append("Mention a second, unrelated small annoyance in passing (one sentence).")
    if s.difficulty.get("has_log"):
        lines.append(
            "Put 3 to 8 lines of raw log or error output the user copied into `attachment_text`: "
            "timestamps in 2026, error codes and messages exactly as a system prints them. The log must "
            "NOT explain the cause or mention a fix."
        )
    else:
        lines.append("Leave `attachment_text` empty.")
    lines.append(f"Length: subject 3 to 8 words. Write the body as {sentences_for(target_words)} full "
                 f"sentences in `body_sentences` (about {target_words} words in total).")
    return "\n\n".join(lines)


def inject_typos(text: str, rng: random.Random, rate: float = 0.05) -> str:
    """Deterministic keyboard slips on about `rate` of longer words: swap, drop or double
    a letter. Error codes and words with digits are left intact so the ticket stays solvable."""
    out = []
    for word in text.split(" "):
        if len(word) > 3 and word.isalpha() and rng.random() < rate:
            i = rng.randrange(1, len(word) - 1)
            op = rng.choice(("swap", "drop", "double"))
            if op == "swap":
                word = word[:i] + word[i + 1] + word[i] + word[i + 2:]
            elif op == "drop":
                word = word[:i] + word[i + 1:]
            else:
                word = word[:i] + word[i] + word[i:]
        out.append(word)
    return " ".join(out)


def _difficulty(rng: random.Random, ticket_type: str) -> dict:
    return {
        "typos": rng.random() < 0.35,
        "vague": ticket_type == "C2" or rng.random() < 0.15,
        "multi_issue": rng.random() < 0.15,
        "has_log": ticket_type != "C2" and rng.random() < 0.20,
    }


def plan_scenarios(n_tickets: int, seed: int = 13, departments: set[str] | None = None) -> list[Scenario]:
    """Spread scenarios over types by TYPE_SHARES and over the available articles."""
    rng = random.Random(seed)
    tax = load_taxonomy()
    articles = [a for a in load_articles() if a.is_v2 and (departments is None or a.meta["department"] in departments)]
    served = [a for a in articles if a.served]
    withheld = [a for a in articles if not a.served]
    depts = sorted({t.department for t in tax.topics if departments is None or t.department in departments})

    scenarios: list[Scenario] = []
    counter = 0
    for ticket_type, share in TYPE_SHARES.items():
        n_scen = max(1, math.ceil(n_tickets * share / PARAPHRASES_PER_SCENARIO))
        pool = {"A": served, "B": served, "C1": withheld, "C2": []}[ticket_type]
        if ticket_type in ("A", "B", "C1") and not pool:
            continue
        order = rng.sample(pool, len(pool)) if pool else []
        for i in range(n_scen):
            counter += 1
            article = order[i % len(order)] if order else None
            dept = article.meta["department"] if article else depts[i % len(depts)]
            scenarios.append(
                Scenario(
                    group_id=f"G-{counter:04d}",
                    type=ticket_type,
                    department=dept,
                    priority=rng.choices(list(PRIORITY_WEIGHTS), weights=list(PRIORITY_WEIGHTS.values()))[0],
                    article=article,
                    c2_kind=("vague", "out_of_scope")[i % 2] if ticket_type == "C2" else None,
                    theme=(
                        C2_THEMES[dept][(i // 2) % len(C2_THEMES[dept])]
                        if ticket_type == "C2" and i % 2 == 1 and dept in C2_THEMES
                        else None
                    ),
                    difficulty=_difficulty(rng, ticket_type),
                )
            )
    return scenarios


def _attempt(client: LLMClient, s: Scenario, persona: str, target_words: int, seed: int) -> dict | None:
    resp = client.complete(
        LLMRequest(
            system=SYSTEM,
            user=build_prompt(s, persona, target_words),
            temperature=0.8,
            max_tokens=600,
            seed=seed,
            json_schema=schema_for(target_words),
        )
    )
    try:
        out = json.loads(resp.text)
    except json.JSONDecodeError:
        return None
    subject = " ".join(str(out.get("subject", "")).split())
    sentences = [" ".join(str(x).split()) for x in out.get("body_sentences", [])]
    # Small models sometimes spill JSON into a sentence ('attachment_text": ""'); drop those.
    body = " ".join(x for x in sentences if x and not _JSON_SPILL.search(x))
    uncovered = str(out.get("uncovered_question") or "").strip()
    if not subject or not body or (s.type == "B" and not uncovered.endswith("?")):
        return None
    attachment = str(out.get("attachment_text") or "").strip()
    if copies_article(f"{subject} {body} {uncovered}", s.article):
        return None
    if attachment and copies_article(attachment, s.article, n=4):
        return None  # a pasted log must not contain the diagnosis
    return {"subject": subject, "body": body, "uncovered": uncovered, "attachment": attachment}


def generate(
    scenarios: list[Scenario], client: LLMClient, n_tickets: int, seed: int = 13, stats: dict | None = None
) -> list[TicketRecord]:
    rng = random.Random(seed)
    quotas = type_quotas(n_tickets)
    made: dict[str, int] = dict.fromkeys(quotas, 0)
    stats = stats if stats is not None else {}
    stats.update(rejected=0, failed=0)
    records: list[TicketRecord] = []
    for s in scenarios:
        personas = random.Random(f"{seed}-{s.group_id}").sample(PERSONAS, PARAPHRASES_PER_SCENARIO)
        for k, persona in enumerate(personas):
            if made.get(s.type, 0) >= quotas.get(s.type, 0):
                break
            target_words = sample_body_length(rng)
            out = None
            for attempt in range(MAX_ATTEMPTS):
                out = _attempt(client, s, persona, target_words, int(s.group_id[2:]) * 100 + k * 10 + attempt)
                if out is not None:
                    break
                stats["rejected"] += 1
            if out is None:
                stats["failed"] += 1
                continue
            body = out["body"]
            uncovered = out["uncovered"] if s.type == "B" else None
            if uncovered:
                # Type B by construction: the unanswerable question is always in the ticket.
                body = f"{body.rstrip()} {uncovered}"
            if s.difficulty.get("typos"):
                body = inject_typos(body, rng)
            attachment = out["attachment"] if s.difficulty.get("has_log") and out["attachment"] else None
            made[s.type] += 1
            records.append(
                TicketRecord(
                    ticket_id=f"T-{len(records) + 1:05d}",
                    group_id=s.group_id,
                    text=f"{out['subject']}\n\n{body}",
                    subject=out["subject"],
                    body=body,
                    attachment_text=attachment,
                    department=s.department,
                    priority=s.priority,
                    type=s.type,
                    gold_articles=[s.article.id] if s.article and s.article.id else [],
                    topic=s.article.topic if s.article else None,
                    difficulty=s.difficulty,
                    uncovered_question=uncovered,
                    persona=persona,
                    prompt_version=PROMPT_VERSION,
                    model=client.model,
                )
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--departments", nargs="*", default=None)
    parser.add_argument("--out", default="data/benchmark/tickets_v0.jsonl")
    args = parser.parse_args()

    client = get_llm_client()
    scenarios = plan_scenarios(args.n, args.seed, set(args.departments) if args.departments else None)
    stats: dict = {}
    records = generate(scenarios, client, args.n, args.seed, stats)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    by_type: dict[str, int] = {}
    for r in records:
        by_type[r.type] = by_type.get(r.type, 0) + 1
    print(f"{len(records)} tickets from {len(scenarios)} scenarios -> {out}  by type {by_type}  "
          f"(attempts rejected: {stats['rejected']}, paraphrases dropped: {stats['failed']})")


if __name__ == "__main__":
    main()

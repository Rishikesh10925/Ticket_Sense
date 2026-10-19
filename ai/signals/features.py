"""The signal vector (Blueprint V2 §9 stage 6 and §13.2; Roadmap Week 7, Rishikesh).

One pure function, `extract`, turns everything the pipeline knows about a draft into
named numeric features. The live pipeline and the offline batch both call it, so a
model trained offline sees exactly the features it will be served.

Groups (§13.2):

    retrieval   top-1 and top-k fused scores, first-second gap, distinct source articles,
                keyword/dense agreement, top-1 dense similarity
    reranker    cross-encoder score of the best passage, spread and first-second gap
    grounding   share of supported claims, minimum and mean support, cited-step share,
                can-answer and schema flags, draft size
    consistency agreement across sampled drafts (filled in when samples exist)
    routing     classifier maximum probability and entropy, cross-department probe and
                its margin below the in-department match
    evidence    age of the cited articles, cited passage length, warning in a cited passage
    ticket      length, number of distinct questions, error code, pasted log

Category history (past acceptance rate by department and topic) needs labels and is
added at training time from the training split only, so it cannot leak.

A missing signal is None, never a made-up default; the model decides how to treat it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

FEATURE_VERSION = "features-v1"
SUPPORTED = 0.5

_WARNING = re.compile(r"(?im)^##\s*warnings?\b|\bwarning:")
_ERROR_CODE = re.compile(r"\b(?:0x[0-9a-f]{4,}|[A-Z]{2,5}[- ]?\d{2,5}|error\s+\d{2,5}|ORA-\d+|HTTP\s?[45]\d\d|status\s+\d{2,3})\b",
                         re.IGNORECASE)


@dataclass(frozen=True)
class Candidate:
    """One fused retrieval candidate, as logged in retrieval_hits."""

    article_key: str | None
    keyword_rank: int | None
    dense_rank: int | None
    dense_score: float | None
    fused_score: float
    rerank_score: float | None
    final_rank: int | None
    updated_at: datetime | None = None
    text: str = ""


@dataclass
class SignalInput:
    candidates: list[Candidate]
    steps: list[dict]
    claims: list[dict]  # {"support": float | None, "cited": [int]}
    can_answer: bool | None
    schema_valid: bool
    missing_information: list[str]
    ticket_text: str
    attachment_text: str | None = None
    probe_top1: float | None = None
    classification: dict | None = None  # classify node output
    consistency: float | None = None
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _sigmoid(x: float | None) -> float | None:
    return None if x is None else 1 / (1 + math.exp(-x))


def _round(features: dict) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in features.items()}


def _retrieval(cands: list[Candidate]) -> dict:
    final = sorted((c for c in cands if c.final_rank is not None), key=lambda c: c.final_rank)
    fused = sorted((c.fused_score for c in cands), reverse=True)
    kw = sorted((c for c in cands if c.keyword_rank is not None), key=lambda c: c.keyword_rank)
    dn = sorted((c for c in cands if c.dense_rank is not None), key=lambda c: c.dense_rank)
    kw5 = {c.article_key for c in kw[:5]}
    dn5 = {c.article_key for c in dn[:5]}
    return {
        "ret_top1_fused": fused[0] if fused else None,
        "ret_topk_fused_mean": sum(fused[:5]) / len(fused[:5]) if fused else None,
        "ret_fused_gap12": fused[0] - fused[1] if len(fused) > 1 else None,
        "ret_distinct_articles": len({c.article_key for c in final}) if final else 0,
        "ret_top1_agree": float(kw[0].article_key == dn[0].article_key) if kw and dn else None,
        "ret_top5_overlap": len(kw5 & dn5) / len(kw5 | dn5) if kw5 | dn5 else None,
        "ret_top1_dense": final[0].dense_score if final else None,
    }


def _reranker(cands: list[Candidate]) -> dict:
    scores = [c.rerank_score for c in sorted((c for c in cands if c.final_rank), key=lambda c: c.final_rank)
              if c.rerank_score is not None]
    return {
        "rr_top1": _sigmoid(scores[0]) if scores else None,
        "rr_spread": scores[0] - scores[-1] if len(scores) > 1 else None,
        "rr_gap12": scores[0] - scores[1] if len(scores) > 1 else None,
    }


def _grounding(inp: SignalInput) -> dict:
    supports = [c["support"] for c in inp.claims if c.get("support") is not None]
    return {
        "gr_supported_share": sum(s >= SUPPORTED for s in supports) / len(supports) if supports else None,
        "gr_min_support": min(supports) if supports else None,
        "gr_mean_support": sum(supports) / len(supports) if supports else None,
        "gr_cited_step_share": (sum(1 for s in inp.steps if s.get("citations")) / len(inp.steps)) if inp.steps else None,
        "gr_can_answer": None if inp.can_answer is None else float(inp.can_answer),
        "gr_schema_valid": float(inp.schema_valid),
        "gr_n_steps": len(inp.steps),
        "gr_n_claims": len(inp.claims),
        "gr_n_missing": len(inp.missing_information),
    }


def _routing(inp: SignalInput, cands: list[Candidate]) -> dict:
    dept = (inp.classification or {}).get("department") or {}
    top1 = next((c.dense_score for c in sorted(cands, key=lambda c: c.final_rank or 99) if c.dense_score is not None), None)
    return {
        "rt_dept_max_prob": dept.get("max_prob"),
        "rt_dept_entropy": dept.get("entropy"),
        "rt_probe_top1": inp.probe_top1,
        "rt_probe_margin": (top1 - inp.probe_top1) if top1 is not None and inp.probe_top1 is not None else None,
    }


def _evidence(inp: SignalInput, cands: list[Candidate]) -> dict:
    by_rank = {c.final_rank: c for c in cands if c.final_rank is not None}
    cited = [by_rank[n] for n in {n for s in inp.steps for n in s.get("citations", [])} if n in by_rank]
    ages = [(inp.now - c.updated_at).days for c in cited if c.updated_at is not None]
    return {
        "ev_cited_age_days_max": float(max(ages)) if ages else None,
        "ev_cited_words_mean": sum(len(c.text.split()) for c in cited) / len(cited) if cited else None,
        "ev_cited_has_warning": float(any(_WARNING.search(c.text) for c in cited)) if cited else None,
    }


def _ticket(inp: SignalInput) -> dict:
    text = inp.ticket_text + ("\n" + inp.attachment_text if inp.attachment_text else "")
    return {
        "tk_words": len(inp.ticket_text.split()),
        "tk_questions": inp.ticket_text.count("?"),
        "tk_has_error_code": float(bool(_ERROR_CODE.search(text))),
        "tk_has_log": float(bool(inp.attachment_text)),
    }


def extract(inp: SignalInput) -> dict:
    features = {"feature_version": FEATURE_VERSION}
    features |= _retrieval(inp.candidates)
    features |= _reranker(inp.candidates)
    features |= _grounding(inp)
    features |= {"cs_agreement": inp.consistency}
    features |= _routing(inp, inp.candidates)
    features |= _evidence(inp, inp.candidates)
    features |= _ticket(inp)
    return _round(features)


FEATURE_NAMES = [k for k in extract(SignalInput([], [], [], None, False, [], "")) if k != "feature_version"]

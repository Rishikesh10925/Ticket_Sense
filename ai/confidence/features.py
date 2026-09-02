"""Confidence-model feature engineering.

Computes the five reliability signals a generated draft is scored on — retrieval
relevance, ticket-to-resolution similarity, document freshness, OCR confidence, and
category risk — from data already available at draft time (the retrieved evidence,
the ticket's OCR result, and the routed department). See docs/confidence-model.md for
the full rationale, and docs/architecture.md for why these are external signals rather
than the LLM's own self-assessment.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

# 1 - each department's measured department-classifier macro-avg F1
# (docs/classification-metrics.md). Grounded in real measured accuracy, not a guess: a
# department the classifier struggles with is a department where "is this ticket even
# in the right queue" is itself uncertain, which should push confidence down
# independent of how good the retrieved evidence looks.
CATEGORY_RISK = {
    "Networking": 0.04,
    "HR": 0.56,
    "Cloud": 0.45,
    "SAP": 0.71,
    "Database": 1.00,
}
DEFAULT_CATEGORY_RISK = 1.0  # unrouted/unrecognized department: maximum risk

FRESHNESS_HALF_LIFE_DAYS = 180.0  # a KB article/resolved ticket is "half as fresh" after ~6 months

# Fixed feature order, shared by ConfidenceFeatures.to_vector(), train.py, and
# predict.py — all three must agree on this order for the model's coefficients to mean
# anything.
FEATURE_NAMES = [
    "retrieval_relevance",
    "ticket_resolution_similarity",
    "document_freshness",
    "ocr_confidence",
    "category_risk",
]


@dataclass
class ConfidenceFeatures:
    retrieval_relevance: float
    ticket_resolution_similarity: float
    document_freshness: float
    ocr_confidence: float
    category_risk: float

    def to_dict(self) -> dict:
        return {
            "retrieval_relevance": self.retrieval_relevance,
            "ticket_resolution_similarity": self.ticket_resolution_similarity,
            "document_freshness": self.document_freshness,
            "ocr_confidence": self.ocr_confidence,
            "category_risk": self.category_risk,
        }

    def to_vector(self) -> list[float]:
        # Fixed order — must match what train.py trained the model on and what
        # predict.py feeds back in.
        return [
            self.retrieval_relevance,
            self.ticket_resolution_similarity,
            self.document_freshness,
            self.ocr_confidence,
            self.category_risk,
        ]


def _freshness(updated_at: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    days_old = max(0.0, (now - updated_at).total_seconds() / 86400)
    return FRESHNESS_HALF_LIFE_DAYS / (FRESHNESS_HALF_LIFE_DAYS + days_old)


def compute_features(
    evidence: Sequence,  # list[embeddings.retrieve.EvidenceResult]
    ocr_confidence: float | None,
    department_name: str | None,
    now: datetime | None = None,
) -> ConfidenceFeatures:
    if not evidence:
        retrieval_relevance = 0.0
        ticket_resolution_similarity = 0.0
        document_freshness = 0.0
    else:
        # pgvector's cosine_distance is 1 - cosine_similarity; clipped at 0 since
        # normalized-embedding distances can exceed 1 for weakly-related pairs, which
        # would otherwise read as "negative similarity".
        similarities = [max(0.0, 1 - item.distance) for item in evidence]
        retrieval_relevance = sum(similarities) / len(similarities)

        resolved = [item for item in evidence if item.source_type == "resolved_ticket"]
        ticket_resolution_similarity = max(
            (max(0.0, 1 - item.distance) for item in resolved), default=0.0
        )

        document_freshness = sum(_freshness(item.updated_at, now) for item in evidence) / len(evidence)

    # No attachment means nothing OCR could have gotten wrong — treated as full
    # confidence rather than penalized, the same rule already used when persisting
    # confidence_features in Week 7's pipeline.
    resolved_ocr_confidence = 1.0 if ocr_confidence is None else ocr_confidence

    category_risk = (
        CATEGORY_RISK.get(department_name, DEFAULT_CATEGORY_RISK)
        if department_name
        else DEFAULT_CATEGORY_RISK
    )

    return ConfidenceFeatures(
        retrieval_relevance=retrieval_relevance,
        ticket_resolution_similarity=ticket_resolution_similarity,
        document_freshness=document_freshness,
        ocr_confidence=resolved_ocr_confidence,
        category_risk=category_risk,
    )

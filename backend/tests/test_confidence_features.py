import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

AI_EMBEDDINGS_DIR = Path(__file__).resolve().parents[2] / "ai" / "embeddings"
AI_CONFIDENCE_DIR = Path(__file__).resolve().parents[2] / "ai" / "confidence"
sys.path.insert(0, str(AI_EMBEDDINGS_DIR))
sys.path.insert(0, str(AI_CONFIDENCE_DIR))

from retrieve import EvidenceResult  # noqa: E402
from features import CATEGORY_RISK, ConfidenceFeatures, compute_features  # noqa: E402
from synthetic_labels import simulate_outcome, success_probability  # noqa: E402
from predict import predict_confidence  # noqa: E402

NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _evidence(source_type: str, distance: float, days_old: int = 0) -> EvidenceResult:
    return EvidenceResult(
        source_type=source_type,
        source_id=uuid.uuid4(),
        title="Some article",
        snippet="content",
        department_id=uuid.uuid4(),
        distance=distance,
        updated_at=NOW - timedelta(days=days_old),
    )


def test_compute_features_with_no_evidence_is_all_zero():
    features = compute_features([], ocr_confidence=None, department_name="Networking", now=NOW)
    assert features.retrieval_relevance == 0.0
    assert features.ticket_resolution_similarity == 0.0
    assert features.document_freshness == 0.0
    assert features.ocr_confidence == 1.0  # no attachment -> not penalized
    assert features.category_risk == CATEGORY_RISK["Networking"]


def test_compute_features_averages_retrieval_relevance():
    evidence = [_evidence("knowledge_base", distance=0.1), _evidence("knowledge_base", distance=0.3)]
    features = compute_features(evidence, ocr_confidence=None, department_name="HR", now=NOW)
    assert features.retrieval_relevance == (0.9 + 0.7) / 2


def test_compute_features_resolution_similarity_only_from_resolved_tickets():
    evidence = [
        _evidence("knowledge_base", distance=0.05),  # closer, but wrong source_type
        _evidence("resolved_ticket", distance=0.4),
    ]
    features = compute_features(evidence, ocr_confidence=None, department_name="HR", now=NOW)
    assert features.ticket_resolution_similarity == 0.6  # 1 - 0.4, not the KB item


def test_compute_features_freshness_decays_with_age():
    fresh = compute_features([_evidence("knowledge_base", 0.1, days_old=0)], None, "HR", now=NOW)
    stale = compute_features([_evidence("knowledge_base", 0.1, days_old=365)], None, "HR", now=NOW)
    assert fresh.document_freshness > stale.document_freshness


def test_compute_features_passes_through_ocr_confidence():
    features = compute_features([], ocr_confidence=0.72, department_name="HR", now=NOW)
    assert features.ocr_confidence == 0.72


def test_compute_features_unknown_department_gets_max_risk():
    features = compute_features([], ocr_confidence=None, department_name="Nonexistent Dept", now=NOW)
    assert features.category_risk == 1.0


def test_feature_vector_order_matches_to_dict():
    features = ConfidenceFeatures(0.1, 0.2, 0.3, 0.4, 0.5)
    assert features.to_vector() == [0.1, 0.2, 0.3, 0.4, 0.5]
    assert list(features.to_dict().values()) == [0.1, 0.2, 0.3, 0.4, 0.5]


def test_synthetic_success_probability_favors_good_evidence():
    good = ConfidenceFeatures(
        retrieval_relevance=0.9, ticket_resolution_similarity=0.9,
        document_freshness=0.9, ocr_confidence=1.0, category_risk=0.04,
    )
    bad = ConfidenceFeatures(
        retrieval_relevance=0.1, ticket_resolution_similarity=0.0,
        document_freshness=0.1, ocr_confidence=0.5, category_risk=1.0,
    )
    assert success_probability(good) > success_probability(bad)


def test_simulate_outcome_is_reproducible_with_seeded_rng():
    features = ConfidenceFeatures(0.8, 0.8, 0.8, 1.0, 0.1)
    a = simulate_outcome(features, random.Random(42))
    b = simulate_outcome(features, random.Random(42))
    assert a == b


def test_predict_confidence_returns_a_probability():
    features = ConfidenceFeatures(0.7, 0.5, 0.6, 1.0, 0.2)
    score = predict_confidence(features)
    assert 0.0 <= score <= 1.0

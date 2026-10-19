from datetime import datetime, timedelta, timezone

from signals.features import FEATURE_NAMES, FEATURE_VERSION, Candidate, SignalInput, extract

NOW = datetime(2026, 12, 1, tzinfo=timezone.utc)


def _cands():
    return [
        Candidate("NET-VPN-001", 1, 1, 0.82, 0.032, 4.0, 1, NOW - timedelta(days=30),
                  "Restart the client.\n## Warnings\nDo not reset the token."),
        Candidate("NET-VPN-002", 2, 3, 0.70, 0.030, 1.0, 2, NOW - timedelta(days=400), "Check the adapter."),
        Candidate("NET-DNS-001", 4, 2, 0.66, 0.029, -2.0, 3, None, "Flush DNS."),
        Candidate("NET-WIFI-001", 3, None, None, 0.016, None, None, None, ""),
    ]


def _input(**kw):
    base = dict(
        candidates=_cands(),
        steps=[{"text": "Restart the client.", "citations": [1]}, {"text": "Check the adapter.", "citations": [2]}],
        claims=[{"support": 0.97, "cited": [1]}, {"support": 0.2, "cited": [2]}],
        can_answer=True,
        schema_valid=True,
        missing_information=[],
        ticket_text="VPN hangs with error 619. Is the server down? Can I work offline?",
        attachment_text="2026-11-30 ERROR 619",
        probe_top1=0.40,
        classification={"department": {"label": "Networking", "max_prob": 0.9, "entropy": 0.2}},
        now=NOW,
    )
    return SignalInput(**(base | kw))


def test_every_group_is_computed():
    f = extract(_input())
    assert f["feature_version"] == FEATURE_VERSION
    assert f["ret_top1_fused"] == 0.032 and f["ret_fused_gap12"] == 0.002
    assert f["ret_distinct_articles"] == 3 and f["ret_top1_agree"] == 1.0
    assert f["rr_top1"] == round(1 / (1 + 2.718281828 ** -4.0), 4) and f["rr_spread"] == 6.0
    assert f["gr_supported_share"] == 0.5 and f["gr_min_support"] == 0.2 and f["gr_cited_step_share"] == 1.0
    assert f["rt_dept_max_prob"] == 0.9 and f["rt_probe_margin"] == 0.42
    assert f["ev_cited_age_days_max"] == 400.0 and f["ev_cited_has_warning"] == 1.0
    assert f["tk_questions"] == 2 and f["tk_has_error_code"] == 1.0 and f["tk_has_log"] == 1.0
    assert f["cs_agreement"] is None  # filled only when consistency samples exist


def test_missing_signals_stay_missing():
    f = extract(_input(candidates=[], claims=[], steps=[], can_answer=False, classification=None, probe_top1=None))
    assert f["ret_top1_fused"] is None and f["rr_top1"] is None and f["gr_supported_share"] is None
    assert f["rt_dept_max_prob"] is None and f["ev_cited_age_days_max"] is None
    assert f["gr_can_answer"] == 0.0 and f["ret_distinct_articles"] == 0


def test_feature_names_are_stable_and_complete():
    assert set(FEATURE_NAMES) == set(extract(_input())) - {"feature_version"}
    assert len(FEATURE_NAMES) == 31

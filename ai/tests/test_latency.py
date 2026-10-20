from evaluation.latency import summarise


def test_summary_reports_median_p90_and_max():
    out = summarise({"draft": [100.0, 200.0, 300.0, 400.0, 5000.0]})
    assert out["draft"] == {"median_ms": 300.0, "p90_ms": 5000.0, "max_ms": 5000.0}

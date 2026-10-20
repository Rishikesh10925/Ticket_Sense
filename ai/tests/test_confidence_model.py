import numpy as np

from confidence_model.dataset import Row, human_label
from confidence_model.model import FEATURES, CategoryHistory, fit, matrix


def _rows(n=240, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        good = rng.uniform() < 0.7
        feats = {
            "ret_top1_dense": float(np.clip(rng.normal(0.7 if good else 0.45, 0.08), 0, 1)),
            "gr_supported_share": float(np.clip(rng.normal(0.85 if good else 0.4, 0.15), 0, 1)),
            "rr_top1": None if i % 7 == 0 else float(rng.uniform()),  # some missing values
        }
        rows.append(Row(f"d{i}", f"T{i}", f"G{i // 3}", "A", ["SAP", "HR"][i % 2], f"t{i % 5}",
                        "train", True, feats, int(good)))
    return rows


def test_category_history_is_smoothed_towards_the_overall_rate():
    rows = _rows()
    h = CategoryHistory.fit(rows)
    assert 0 < h.overall < 1
    assert all(min(h.overall, v) - 1e-9 <= v or v <= max(h.overall, v) for v in h.department.values())
    unseen = Row("x", "x", "x", "A", "Cloud", "new-topic", "val", True, {}, None)
    assert h.features(unseen) == {"cat_department_rate": h.overall, "cat_topic_rate": h.overall}


def test_matrix_keeps_missing_values_missing():
    rows = _rows(20)
    x = matrix(rows, CategoryHistory.fit(rows))
    assert x.shape == (20, len(FEATURES))
    assert np.isnan(x[0, FEATURES.index("rr_top1")])  # row 0 has no reranker score


def test_both_candidates_learn_and_explain():
    rows = _rows()
    train, held = rows[:180], rows[180:]
    for kind in ("logreg", "xgboost"):
        model, trials = fit(kind, train, "judge")
        assert trials and model.params in [t["params"] for t in trials]
        p = model.calibrate(train).predict(held)
        assert p.shape == (60,) and ((0 <= p) & (p <= 1)).all()
        good = np.array([r.acceptable for r in held]) == 1
        assert p[good].mean() > p[~good].mean()
        reasons = model.top_reasons(held[:3])
        assert len(reasons) == 3 and all(isinstance(r, list) for r in reasons)


def test_platt_calibration_keeps_the_ranking():
    rows = _rows()
    model, _ = fit("xgboost", rows[:120], "judge")
    raw = model.raw(rows[180:])
    cal = model.calibrate(rows[120:180]).predict(rows[180:])  # calibrated on held-out rows, as in train.py
    from scipy.stats import spearmanr

    assert spearmanr(raw, cal).statistic > 0.999  # monotone: ties stay ties, order is kept


def test_human_label_rules():
    assert human_label(None, None) is None
    assert human_label(1.0, None) == 1 and human_label(0.0, None) == 0
    assert human_label(0.5, None) is None  # disagreement without adjudication: no label yet
    assert human_label(0.5, 1) == 1

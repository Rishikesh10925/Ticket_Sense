import numpy as np
import pytest

from signals.baselines import B7, DraftSignals, baseline_scores, compare


def _signals(n=60, seed=0):
    rng = np.random.default_rng(seed)
    out, acceptable = [], []
    for i in range(n):
        good = i % 2 == 0
        out.append(
            DraftSignals(
                draft_id=f"d{i}", ticket_id=f"t{i}", group_id=f"g{i // 3}",
                top1_similarity=float(np.clip((0.75 if good else 0.45) + rng.normal(0, 0.08), 0, 1)),
                top1_rerank=float((3.0 if good else -2.0) + rng.normal(0, 1.5)),
                groundedness=float(np.clip((0.9 if good else 0.4) + rng.normal(0, 0.15), 0, 1)),
            )
        )
        acceptable.append(good)
    return out, acceptable


def test_scores_have_one_value_per_draft_and_missing_signals_count_as_zero():
    sig = [DraftSignals("d", "t", "g", None, None, None), DraftSignals("e", "t", "g", 0.8, 0.0, 1.0)]
    scores = baseline_scores(sig)
    assert scores["B4"].tolist() == [0.0, 0.8]
    assert scores["B5"].tolist() == [0.0, 0.5]  # sigmoid(0)
    assert scores["B6"].tolist() == [0.0, 1.0]
    assert scores["B0-show"].tolist() == [1.0, 1.0]


def test_informative_signals_beat_the_trivial_baseline():
    sig, acc = _signals()
    table = compare(baseline_scores(sig), acc, [s.group_id for s in sig], n_boot=200)
    for name in ("B4", "B5", "B6"):
        assert table[name]["aurc"] < table["B0-show"]["aurc"]
        assert table[name]["auroc_unacceptable"] > 0.7
        low, high = table[name]["aurc_ci"]
        assert low <= table[name]["aurc"] <= high


def test_b7_fits_on_calibration_and_scores_held_out_drafts():
    calib, calib_acc = _signals(seed=1)
    test, test_acc = _signals(seed=2)
    model = B7().fit(calib, calib_acc)
    p = model.predict(test)
    assert p.shape == (len(test),) and ((0 <= p) & (p <= 1)).all()
    assert all(c > 0 for c in model.coefficients.values())
    table = compare({"B7": p}, test_acc, [s.group_id for s in test], n_boot=200)
    assert table["B7"]["auroc_unacceptable"] > 0.8


def test_b7_refuses_single_class_calibration():
    sig, _ = _signals(n=6)
    with pytest.raises(ValueError):
        B7().fit(sig, [True] * 6)


def test_csv_roundtrip_keeps_missing_values(tmp_path):
    from signals.extract_baselines import read_csv, write_csv

    sig = [DraftSignals("d1", "T-1", "G-1", 0.71, -1.2, None), DraftSignals("d2", "T-2", "G-1", None, None, 0.5)]
    write_csv(sig, tmp_path / "b.csv")
    assert read_csv(tmp_path / "b.csv") == sig

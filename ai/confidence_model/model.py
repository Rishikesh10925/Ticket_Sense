"""The confidence model (Blueprint V2 §13; Roadmap Week 8, Shivaganesh).

Predicts the probability that a draft is acceptable from its signal vector. Two
candidates are trained and compared, as the blueprint asks:

    logistic regression   interpretable; median imputation plus missing-value flags
    gradient boosting     XGBoost; handles missing values natively

Hyperparameters are chosen by group-aware cross-validation on the train split (folds
never split a scenario's paraphrases). Scores are then calibrated with Platt
scaling on the calibration split. Category history (§13.2: past acceptance rate of
the department and topic) is learned from the training labels only and added as two
features, smoothed towards the overall rate so rare topics do not get extreme values.

`top_reasons` names the signals that pulled a draft's score down the most, so the
workbench can say why a draft was down-ranked (§13.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from signals.features import FEATURE_NAMES

MODEL_VERSION = "confidence-v1"
HISTORY = ("cat_department_rate", "cat_topic_rate")
FEATURES = [*FEATURE_NAMES, *HISTORY]
SMOOTHING = 20  # pseudo-count pulling a category's rate towards the overall rate

READABLE = {
    "ret_top1_dense": "weak best retrieval match", "ret_top1_fused": "weak fused retrieval score",
    "ret_fused_gap12": "no clear best passage", "ret_top1_agree": "keyword and dense search disagree",
    "ret_top5_overlap": "keyword and dense results differ", "ret_distinct_articles": "evidence spread over many articles",
    "rr_top1": "low reranker score", "rr_gap12": "no clear best passage (reranker)", "rr_spread": "flat reranker scores",
    "gr_supported_share": "unsupported claims", "gr_min_support": "a weakly supported claim",
    "gr_mean_support": "low claim support", "gr_can_answer": "model says it cannot answer",
    "gr_n_missing": "information missing", "cs_agreement": "samples disagree",
    "rt_dept_max_prob": "uncertain routing", "rt_dept_entropy": "uncertain routing",
    "rt_probe_margin": "another department matches as well", "ev_cited_age_days_max": "old evidence",
    "cat_department_rate": "department often needs rework", "cat_topic_rate": "topic often needs rework",
    "ret_topk_fused_mean": "weak retrieval overall", "gr_cited_step_share": "steps without citations",
    "gr_schema_valid": "draft failed its format check", "gr_n_steps": "unusual number of steps",
    "gr_n_claims": "unusual number of claims", "rt_probe_top1": "ticket also matches another department",
    "ev_cited_words_mean": "unusual evidence length", "ev_cited_has_warning": "cited evidence carries a warning",
    "tk_words": "unusual ticket length", "tk_questions": "ticket asks several questions",
    "tk_has_error_code": "error code in the ticket", "tk_has_log": "pasted log in the ticket",
}


@dataclass
class CategoryHistory:
    overall: float = 0.5
    department: dict = field(default_factory=dict)
    topic: dict = field(default_factory=dict)

    @classmethod
    def fit(cls, rows) -> "CategoryHistory":
        y = np.array([r.acceptable for r in rows], dtype=float)
        overall = float(y.mean())

        def rates(key):
            groups: dict = {}
            for r in rows:
                groups.setdefault(key(r), []).append(r.acceptable)
            return {k: (sum(v) + SMOOTHING * overall) / (len(v) + SMOOTHING) for k, v in groups.items()}

        return cls(overall, rates(lambda r: r.department), rates(lambda r: r.topic))

    def features(self, row) -> dict:
        return {"cat_department_rate": self.department.get(row.department, self.overall),
                "cat_topic_rate": self.topic.get(row.topic, self.overall)}


def matrix(rows, history: CategoryHistory) -> np.ndarray:
    out = np.full((len(rows), len(FEATURES)), np.nan)
    for i, r in enumerate(rows):
        values = r.features | history.features(r)
        for j, name in enumerate(FEATURES):
            v = values.get(name)
            if v is not None:
                out[i, j] = float(v)
    return out


def make_estimator(kind: str, params: dict):
    if kind == "logreg":
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        return make_pipeline(SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                             StandardScaler(), LogisticRegression(C=params["C"], max_iter=2000))
    if kind == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(n_estimators=params["n_estimators"], max_depth=params["max_depth"],
                             learning_rate=params["learning_rate"], subsample=0.9, colsample_bytree=0.9,
                             eval_metric="logloss", random_state=2026, n_jobs=1)  # 1 thread: bit-for-bit reproducible
    raise ValueError(kind)


GRIDS = {
    "logreg": [{"C": c} for c in (0.03, 0.1, 0.3, 1.0, 3.0)],
    "xgboost": [{"n_estimators": n, "max_depth": d, "learning_rate": lr}
                for n in (100, 300) for d in (2, 3, 4) for lr in (0.05, 0.1)],
}


class PlattCalibrator:
    """Logistic regression on the logit of the raw score."""

    def fit(self, raw: np.ndarray, y: np.ndarray) -> "PlattCalibrator":
        from sklearn.linear_model import LogisticRegression

        # Regularised (C=1): an unregularised fit saturates at exactly 0 or 1 on separable
        # data, which turns distinct scores into ties.
        self.lr = LogisticRegression(C=1.0, max_iter=1000).fit(_logit(raw).reshape(-1, 1), y)
        return self

    def predict(self, raw: np.ndarray) -> np.ndarray:
        return self.lr.predict_proba(_logit(raw).reshape(-1, 1))[:, 1]


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


@dataclass
class ConfidenceModel:
    kind: str
    params: dict
    estimator: object
    history: CategoryHistory
    calibrator: object | None = None
    label_source: str = "judge"
    version: str = MODEL_VERSION

    def raw(self, rows) -> np.ndarray:
        return self.estimator.predict_proba(matrix(rows, self.history))[:, 1]

    def predict(self, rows) -> np.ndarray:
        raw = self.raw(rows)
        return self.calibrator.predict(raw) if self.calibrator is not None else raw

    def calibrate(self, rows) -> "ConfidenceModel":
        """Platt scaling on the calibration split. Isotonic regression was tried first and
        turned scores into steps; the ties raised validation AURC from 0.151 to 0.187.
        Platt is strictly monotone, so calibration cannot change the ranking."""
        y = np.array([r.acceptable for r in rows], dtype=float)
        self.calibrator = PlattCalibrator().fit(self.raw(rows), y)
        return self

    def contributions(self, rows) -> np.ndarray:
        """Per-feature contribution to each draft's (log-odds) score; negative pulls down."""
        x = matrix(rows, self.history)
        if self.kind == "xgboost":
            import xgboost

            return self.estimator.get_booster().predict(xgboost.DMatrix(x), pred_contribs=True)[:, : len(FEATURES)]
        imputer, scaler, lr = self.estimator[0], self.estimator[1], self.estimator[2]
        z = scaler.transform(imputer.transform(x))
        return (z * lr.coef_[0])[:, : len(FEATURES)]

    def top_reasons(self, rows, k: int = 3) -> list[list[str]]:
        out = []
        for c in self.contributions(rows):
            order = np.argsort(c)
            out.append([READABLE.get(FEATURES[j], FEATURES[j]) for j in order[:k] if c[j] < 0])
        return out


def group_cv_score(kind: str, params: dict, rows, n_splits: int = 5) -> float:
    """Mean AURC over group k-fold on the training rows (lower is better)."""
    from sklearn.model_selection import GroupKFold

    from evaluation.metrics import aurc

    y = np.array([r.acceptable for r in rows], dtype=float)
    groups = np.array([r.group_id for r in rows])
    scores = []
    for tr, te in GroupKFold(n_splits=n_splits).split(np.zeros(len(rows)), y, groups):
        train_rows = [rows[i] for i in tr]
        history = CategoryHistory.fit(train_rows)  # history from the fold's training part only
        est = make_estimator(kind, params).fit(matrix(train_rows, history), y[tr])
        scores.append(aurc(est.predict_proba(matrix([rows[i] for i in te], history))[:, 1], y[te]))
    return float(np.mean(scores))


def fit(kind: str, train_rows, label_source: str) -> tuple[ConfidenceModel, list[dict]]:
    trials = [{"params": p, "cv_aurc": round(group_cv_score(kind, p, train_rows), 4)} for p in GRIDS[kind]]
    best = min(trials, key=lambda t: t["cv_aurc"])
    history = CategoryHistory.fit(train_rows)
    y = np.array([r.acceptable for r in train_rows], dtype=float)
    estimator = make_estimator(kind, best["params"]).fit(matrix(train_rows, history), y)
    return ConfidenceModel(kind, best["params"], estimator, history, label_source=label_source), trials

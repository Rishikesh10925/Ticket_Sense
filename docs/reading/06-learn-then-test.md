# Reading note: Learn then Test

- Paper: A. N. Angelopoulos, S. Bates, E. J. Candès, M. I. Jordan and L. Lei,
  "Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control",
  arXiv:2110.01052, 2021 (Blueprint ref. [6])
- Presented by: Shivaganesh, Week 1 design session (10 minutes)

## The idea in one paragraph

Any tunable system has a parameter λ (for us, the confidence threshold). For each
candidate λ, state the null hypothesis "the risk at λ exceeds α". Compute a valid
p-value for it on a calibration set the model never trained on. Then pick λ values whose
nulls are rejected by a procedure that controls the family-wise error rate (FWER) at δ.
Result: with probability at least 1 − δ over the calibration draw, **every** selected λ
has risk ≤ α. No assumption about the model, and the risk does not need to be monotone in λ.

## The three ingredients

1. **Candidate grid** of λ values, fixed before looking at the labels.
2. **p-values.** For a risk that is a rate of bad events (ours: the share of shown drafts
   that are unacceptable), the exact binomial tail P(Bin(n, α) ≤ k) is valid. The paper
   also gives Hoeffding and Hoeffding-Bentkus p-values for general bounded losses.
3. **FWER control.** Bonferroni works but is conservative. **Fixed-sequence testing**
   orders the hypotheses in advance and tests each at the full level δ, stopping at the
   first failure. That needs no correction, and suits us because risk roughly falls as
   the threshold gets stricter.

## How we implemented it (`ai/evaluation/risk_control.py`)

- Order: thresholds from strict to lenient. Keep the most lenient one rejected before the
  first failure.
- Thresholds with fewer than ⌈log δ / log(1 − α)⌉ shown drafts (22 at α = δ = 0.1) can never
  be rejected, even with zero errors, so they are skipped. The skip depends only on the
  scores, not the labels, so validity is kept.
- Unit test `test_learn_then_test_guarantee_holds_on_fresh_exchangeable_data` checks the
  promise empirically: across resplits, the test-side risk exceeds α in at most about δ of them.

## Sample size consequence for our plan

With 200 human-labelled calibration drafts and α = 0.10, certifying a fast lane needs
a high-scoring set with well under 10% errors. For example, 60 shown drafts with
2 unacceptable gives p = P(Bin(60, 0.1) ≤ 2) ≈ 0.05, which is rejected at δ = 0.1. With
fewer labels the fast lane may come out empty. That is an honest outcome, and it is why
the calibration split must not shrink below 200 labels.

## Limits

The guarantee holds when test tickets are exchangeable with calibration tickets. A new
kind of problem (unseen topic) breaks it. H3 measures how badly.

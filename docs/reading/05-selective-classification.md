# Reading note: Selective Classification for Deep Neural Networks

- Paper: Y. Geifman and R. El-Yaniv, NeurIPS 2017 (Blueprint ref. [5])
- Presented by: Aashritha, Week 1 design session (10 minutes)

## The idea in one paragraph

A classifier that may abstain is a pair (f, g): f predicts, and g decides whether to
answer. Lowering how often you answer (coverage) should lower how often you are wrong on
the answers you give (selective risk). The paper builds g by thresholding a confidence
function κ, and asks how to pick the threshold so that the risk stays below a target r*
with high probability, using only a held-out labelled set.

## What they do

1. **Confidence functions.** Softmax response (the top class probability) and Monte Carlo
   dropout variance. On image benchmarks the plain softmax response is a strong,
   cheap baseline.
2. **Selection with Guaranteed Risk (SGR).** A binary search over thresholds on a
   labelled set. At each candidate it computes an upper confidence bound on the true
   selective risk from an exact binomial tail. The δ budget is split across the search
   steps so that the final threshold satisfies risk ≤ r* with probability ≥ 1 − δ.
3. **Risk-coverage curves** as the way to compare confidence functions across all
   thresholds rather than at one hand-picked cutoff.

## What we take for TicketSense

| Paper concept | Our version |
|---|---|
| Coverage / selective risk | Share of tickets that get a shown draft / share of shown drafts that are unacceptable |
| Risk-coverage curve, AURC | Our headline metric (`ai/evaluation/metrics.py`) |
| Softmax response as a strong cheap baseline | Our B4 (top-1 retrieval similarity) plays this role. A win has to beat it |
| SGR's binomial bound | The same exact binomial p-value we use inside Learn-then-Test |

## Limits to keep in mind

- Their setting is classification with a fixed label; ours is free text judged by a rubric.
  The "correctness" label is human and noisy, so agreement (kappa) matters.
- The guarantee assumes new data looks like the calibration data. Our unseen-topic set
  (H3) tests exactly where that breaks.

## Question for the team

The UI has three lanes, not two. Which lane carries the guaranteed budget? Answer agreed
in the session: the fast lane (α = 0.10) is the guaranteed one. The assisted lane gets
its own looser certified budget (α = 0.40); escalation has none.

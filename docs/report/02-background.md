# 2. Background and related work

*Owner: Shivaganesh. Draft v1; expands the Week 1 [literature review](../literature-review.md).*

## 2.1 Retrieval-augmented generation

Retrieval-augmented generation grounds a language model's answer in retrieved passages
(Lewis et al.). TicketSense uses hybrid retrieval (keyword and dense search fused, then a
cross-encoder reranker) and asks the model for structured, cited steps, so every claim can
be checked against the passage it cites.

## 2.2 Confidence and calibration

Language models' own statements of confidence are poorly calibrated. TicketSense therefore
scores drafts with a separate model trained on outcome labels, and calibrates its scores
(Platt scaling) so a score of 0.8 means roughly 80% acceptable. Calibration is measured
with expected calibration error (ECE, 10 equal-width bins) and the Brier score.

## 2.3 Selective prediction and risk control

A system that may abstain is judged by its risk-coverage trade-off: the error rate among
the cases it accepts, as a function of how many it accepts. The area under that curve
(AURC) is the primary metric. To choose thresholds with a guarantee, TicketSense uses
Learn-then-Test (Angelopoulos et al.): candidate thresholds are tested in a fixed sequence
with an exact binomial test, so the error rate above the chosen threshold is at most α
with probability at least 1 − δ, when new tickets resemble the calibration tickets.

## 2.4 Human-AI deferral

Learning-to-defer work studies when a model should hand a case to a human. TicketSense's
escalate lane is a deferral decision; the assisted lane is a middle ground in which the
human sees the draft together with the claims most likely to be wrong.

## 2.5 Groundedness checking

Claim-level entailment checking with an NLI model verifies whether each claim is supported
by the passage it cites. TicketSense uses it both as a signal for the confidence model and
to show the weakest claims to the engineer. An LLM-based checker (`llama3.1:8b`) was
compared with the NLI checker on 495 claims: 81.6% agreement
([llm-groundedness-v1.json](../results/llm-groundedness-v1.json)).

## 2.6 Gaps this project addresses

**To be written**: a short positioning paragraph with full citations. The references list
lives in the blueprint (refs [1] to [21]) and moves to the Appendix.

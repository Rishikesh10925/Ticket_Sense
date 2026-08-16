# Literature review: RAG, confidence calibration, and human-AI deferral

Week 1 research note (Shivaganesh) surveying the three bodies of literature TicketSense's
design draws on, per [docs/architecture.md](architecture.md)'s "why a separate confidence
classifier, not LLM self-confidence" rationale. This is a starting scan for a student
capstone, not an exhaustive systematic review — enough to ground the design decisions
already made, and to point at where TicketSense's approach follows vs. departs from
established practice.

## 1. Retrieval-augmented generation (RAG)

- **Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
  (NeurIPS 2020).** The foundational RAG paper: pairs a retriever over an external
  document index with a generator conditioned on the retrieved passages, so the model's
  output is grounded in retrievable evidence rather than only its parameters. This is the
  core pattern TicketSense's drafting step follows — retrieve department-scoped knowledge
  base/resolved-ticket evidence, then constrain the LLM to draft only from that evidence
  with citations.
- **Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey"
  (2023–24, arXiv).** Surveys the now-common RAG variants (naive, advanced, modular) and
  the failure modes relevant here: retrieval that returns irrelevant passages, and
  generation that ignores or contradicts the retrieved context despite it being present.
  Both failure modes are exactly what the confidence model's "retrieval relevance"
  feature is meant to catch before a low-quality draft reaches a human reviewer.

**Implication for TicketSense:** RAG grounding reduces but does not eliminate ungrounded
generation — it lowers the rate of hallucination, it doesn't guarantee zero. That gap is
the reason a downstream confidence signal is still needed even with retrieval in place,
not a substitute for one.

## 2. Confidence calibration

- **Guo et al., "On Calibration of Modern Neural Networks" (ICML 2017).** Shows that
  modern deep networks are often poorly calibrated — their predicted confidence doesn't
  match their actual accuracy, typically overconfident — and introduces Expected
  Calibration Error (ECE) as a standard metric, plus temperature scaling as a simple
  post-hoc fix. TicketSense's evaluation protocol
  ([research-evaluation.md](research-evaluation.md)) uses ECE for exactly this reason.
- **Kadavath et al., "Language Models (Mostly) Know What They Know" (Anthropic, 2022).**
  Studies LLM self-evaluation directly: models can be reasonably calibrated when asked
  simple, well-scoped self-assessment questions, but calibration degrades on harder,
  more open-ended tasks — and self-reported confidence is sensitive to prompt phrasing in
  ways an external classifier's features are not.
- **Desai & Durrett, "Calibration of Pre-trained Transformers" (EMNLP 2020).** Finds
  pre-trained transformer confidence is more reliable in-distribution than
  out-of-distribution — directly relevant to TicketSense, where a ticket can easily fall
  outside the department's seeded knowledge base.

**Implication for TicketSense:** this literature is the direct justification for
`architecture.md`'s core design choice — an LLM asked to self-rate a specific draft is
exactly the poorly-calibrated, prompt-sensitive, out-of-distribution-fragile case this
research describes. An external classifier trained on measurable retrieval/similarity/
freshness/risk features, and retrainable on logged human outcomes, sidesteps that
failure mode rather than trying to fix the LLM's self-assessment.

## 3. Human-AI deferral / learning to defer

- **Madras, Pitassi & Zemel, "Predict Responsibly: Improving Fairness and Accuracy by
  Learning to Defer" (NeurIPS 2018).** Introduces the "learning to defer" framing: a
  model that can choose to abstain and hand a decision to a human, trained jointly to
  decide *when* deferring beats predicting. TicketSense's confidence gate is a simplified,
  two-model version of this idea — a separate classifier decides whether the drafting
  model's output should reach a human reviewer or be withheld in favor of full escalation.
- **Mozannar & Sontag, "Consistent Estimators for Learning to Defer to an Expert" (ICML
  2020).** Formalizes the deferral objective and shows naive approaches (e.g., training
  a classifier and a rejector independently) can be inconsistent with the true optimal
  deferral policy. Relevant caution for later weeks: TicketSense's confidence model and
  drafting model are trained independently, which this paper suggests is a simplification
  worth being explicit about rather than assuming it's automatically optimal.
- **Bansal et al., "Does the Whole Exceed its Parts? The Effect of AI Explanations on
  Complementary Team Performance" (CHI 2021).** Empirically studies human-AI teams and
  finds that showing an AI's confidence/explanation doesn't automatically improve
  human+AI performance over either alone — it depends on whether the human can actually
  use the signal to decide when to trust or override. Motivates TicketSense's plan to
  show the Department Engineer the retrieved evidence and confidence score, not just an
  accept/reject button, and to log accept/edit/reject/escalate as feedback rather than
  assuming the confidence gate alone is sufficient.

**Implication for TicketSense:** the confidence gate is TicketSense's version of a
learn-to-defer system, deliberately simplified (independent models, a single threshold
rather than a jointly optimized policy) for a one-semester scope — a known simplification
per Mozannar & Sontag, to revisit if time allows rather than presented as solved.

## How this informs current design decisions

All three threads converge on the same conclusion already reflected in
[architecture.md](architecture.md): grounding (RAG) reduces hallucination risk but is not
sufficient on its own, self-reported LLM confidence is not trustworthy for the
autonomy decision, and an external, human-outcome-retrainable classifier making an
explicit defer/don't-defer choice is the more defensible design — consistent with, not
inventing, this line of research.

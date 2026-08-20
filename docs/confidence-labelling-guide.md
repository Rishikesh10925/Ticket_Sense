# Confidence-model outcome labelling guide

Week 3 note (Shivaganesh) drafting the guide that will convert logged human review
actions into training labels for the confidence model, per the project blueprint's
Section 11.1: "an accepted draft with a minor edit counts as a success label; a rejected
or heavily rewritten draft counts as a failure label." **This is a guide for a labelling
process that starts in Weeks 8–11**, once the review UI and `feedback` table are actually
being populated by real reviewer actions — nothing here is applied to data yet, since no
drafts or reviews exist. Drafted now so the `feedback`/`tickets` schema (already live,
see `docs/ticket-lifecycle.md`) is captured with this labelling need in mind, and so
Weeks 8–11 aren't starting the labelling design from zero.

## Why a label is needed at all

The confidence model (not yet built) predicts, from retrieval/similarity/freshness/risk
features computed at draft time, whether a draft is reliable enough to show a human
reviewer. Training it needs a ground-truth outcome label per ticket: did the draft the
model saw actually turn out to be good or not? That label doesn't come from the LLM —
it comes from what the human reviewer actually did with the draft, recorded in the
`feedback` table (`action`, `edited_reply`, `reject_reason`).

## Proposed label mapping

| Reviewer action (`feedback.action`) | Label | Rationale |
|---|---|---|
| `accept` (no edits) | **Success** | The draft was used as-is — the strongest positive signal available. |
| `edit`, minor change | **Success** | A small correction (typo, one added detail) still means the draft was substantively right. |
| `edit`, heavy rewrite | **Failure** | If the reviewer rewrote most of the draft, the original wasn't actually usable — the "edit" action alone doesn't distinguish this from a minor fix, which is why "minor" vs. "heavy" needs its own rule (below). |
| `reject` | **Failure** | Reviewer explicitly discarded the draft. |
| `escalate` | **Excluded from training** | Escalation without an AI draft attached (per `architecture.md`'s confidence gate) means no draft was ever shown to score — there's nothing to label. If escalation ever happens *after* a draft was shown (a reviewer escalating instead of using a shown draft), that case should be labelled the same as `reject`, not excluded — a decision to make explicit once that flow exists. |

## Open question: defining "minor" vs. "heavy" edit

Not resolved this week — recording the options rather than picking one blind, since the
right threshold depends on data this project doesn't have yet:

- **Edit distance ratio** (e.g. Levenshtein distance between `tickets.ai_draft_reply` and
  `feedback.edited_reply`, normalized by length) — simple, cheap, but treats a
  one-word factual correction and a one-word wording tweak the same.
  - Would need a documented threshold (candidate starting point: <15% of characters
  changed = minor) that is picked once results calibrate against reality.
- **Semantic similarity** (embed both versions with the same
  `sentence-transformers/all-MiniLM-L6-v2` model already used for retrieval, compare
  cosine similarity) — better captures meaning-preserving edits vs. content changes, more
  expensive to compute, harder to explain to a non-technical reviewer of the labels.
- **A third explicit reviewer input** — e.g., a lightweight "how much did you change?"
  control in the review UI itself, shifting the judgment to the human instead of an
  automated distance metric. Most accurate, adds UI/workflow scope not currently planned.

Recommendation to revisit in Week 8 with real edit data in hand rather than deciding now:
start with the edit-distance-ratio approach (cheapest to implement, no UI changes), and
only move to semantic similarity or an explicit reviewer input if edit-distance labels
turn out to disagree badly with a manual spot-check.

## What this guide does not cover

- The actual labelling script/pipeline — not written yet, this is the design only.
- Class balance handling (accept is likely to dominate once reviewers trust the system,
  which would make failures rare and the model harder to train well) — a Week 8+ concern
  once real distribution is visible.
- Inter-rater considerations — irrelevant here since labels come from the operational
  reviewer's own action, not a separate labelling pass by multiple people.

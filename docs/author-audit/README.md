# Three-author audit (rubric AUTHOR-v2)

The three student authors independently rate the same frozen drafts on Q1 (acceptability),
Q2 (support from the cited passages) and Q3 (relevance to the ticket). This follows the
"Three-Author Human Annotation Protocol" of 3 November 2026. It is an **author-led
development audit**, not external validation: all three raters built TicketSense.

Authors: Rishikesh (AUTH-R), Aashritha (AUTH-A) and Shivaganesh (AUTH-S).

## Frozen plan (3 November 2026)

[plan_author_v2.json](plan_author_v2.json) records the plan and the hashes of the hidden
manifest and the sample. The manifest and `01_sampling_manifest.csv` stay git-ignored in
`data/annotation/packs/author_v2/` until all ratings are in.

**Sample.** This is the frozen human-audit sample ([../human-audit/](../human-audit/)): Mode H,
N = 40, seed 20261102, at most one answering draft per scenario, validation and unseen-topic
splits only, with the sealed test unread. A new sample disjoint from it is not feasible. Once
its 40 scenarios are removed, the eligible pool has 20 A, 2 B, 48 C1 and **0 C2** scenarios
left, and even N = 20 needs 3 of each type.

**Exposure.** All 40 cases were rated by outside reviewers in two pilot rounds (80
ratings). Those ratings are never shown to the authors, are not pooled with author ratings
and are not used to select or weight anything. They stay a separate exploratory pilot, with
its poor agreement disclosed. Rishikesh ran the selection and the pilot and saw its
agreement summaries. Each page also has a per-case "seen before" box, exported as
`seen_before`.

**Batches.** Batch 1 has 20 cases, the balanced half used for the first outside pair, and
batch 2 has the other 20. Every author rates both batches. Agreement is reported over all 40
once both are in.

**Practice.** There are six training-split drafts outside the sample, chosen from stored
values with seed 20261103:
- two well cited but judged wrong (all claims pass NLI, judge W);
- two partly unsupported (some claims pass and some fail, judge R);
- two correct and supported (all claims pass, judge accepted; the judge never gave A on training drafts).

They are shown only in batch 1, then the authors compare and discuss them, and rubric
AUTHOR-v2 is frozen. Practice never counts toward agreement.

**References.** Each page shows the ticket, attachment text, the full reply and the passages
it cites or retrieved. No separate gold article is shown. Showing one only where an article
exists would reveal the ticket type, which is a C1 versus C2 signal. So Q1 is judged from
these passages, and U is used when they cannot establish correctness.

## Running it

From `backend/`, with the database running:

```bash
python -m app.scripts.author_audit freeze                 # done once; refuses to run again
python -m app.scripts.author_audit export --batch 1       # three pages, one per author
python -m app.scripts.author_audit collect ../data/annotation/returned/author_v2/*.xlsx
```

Each page works offline:
- It shows the full rubric with the protocol's worked examples.
- The order is shuffled per author.
- Reasons are required where AUTHOR-v2 requires them.
- It warns when A or M is given with Q3 = No.
- It records time on screen and whether a reason was pasted.
- Downloading the final file locks the answers on the page.

`collect` keeps each original file in `data/annotation/returned/author_v2/` and writes two
files: `04_agreement_report.json` and `05_adjudication_log.csv`.

The agreement report covers:
- Krippendorff's alpha across the three authors: ordinal for Q1 (A<M<R<W, with U left out
  and counted) and for Q2 (Unclear left out), and nominal for binary Q1 and for Q3;
- scenario-bootstrap 95% intervals;
- 3/3 and 2/3 counts and label distributions;
- independence checks: identical answers and near-identical reasons between authors.

The adjudication log lists every Q1, Q2 and Q3 disagreement, with each author's original
answer and reason and blank columns for the decision.

## Reporting

- A "grounded but unacceptable" finding needs all three original ratings to give Q1 R or W
  and Q2 Fully. A wrong-topic finding also needs all three to give Q3 No.
- Majority and adjudicated cases are reported separately, and unresolved stays unresolved.
- Part I is weighted by eligible scenarios per type. Part II is reported by mechanism only,
  and the two parts are never pooled.
- Adjudication never changes the original ratings.

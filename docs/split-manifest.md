# Split manifest design (v1)

Owner: Shivaganesh. Blueprint V2 §11.5; Roadmap Week 2 "split manifest design with
group ids". Code: [ai/benchmark/splits.py](../ai/benchmark/splits.py). It supersedes the
V1 [split-strategy.md](split-strategy.md).

## Records

Each ticket record (Appendix C.2) carries:

| Field | Meaning |
|---|---|
| `ticket_id` | `T-00001` |
| `group_id` | Scenario id: one source plus one situation. Its paraphrases share it |
| `type` | A, B, C1 or C2, set by construction |
| `gold_articles` | Article ids that answer it, or `[]` for C2 |
| `split` | Filled from the manifest, never by hand |

## The unit of splitting is the leakage group

Blueprint §11.1: "paraphrases of one problem never sit on both sides". A scenario is
one paraphrase family, but two scenarios written from the same article describe nearly
the same problem. So the unit is stricter than the scenario:

- **A, B, C1**: the gold article. Every ticket written from article X lands in one split.
- **C2**: the scenario `group_id` (there is no article).

Consequence: validation, calibration and test tickets come from articles whose tickets
the models never trained on. Retrieval still sees every served article, because the KB is
not split. This is the honest setting: a deployed system meets new tickets about known
documents.

## Targets (1,800-ticket benchmark)

| Split | Seen-topic tickets (A, B, C2) | C1 tickets | Total | Use |
|---|---|---|---|---|
| train | ~840 | 0 | ~840 | Classifier and confidence-model training (judge labels + any human labels) |
| val | ~150 | 0 | ~150 | Model selection, feature decisions |
| calib | ~250 | 0 | ~250 | Probability calibration, Learn-then-Test thresholds |
| test (locked) | ~200 | ~50 | ~250 | Final headline numbers, evaluated once in Week 10 |
| unseen | 0 | ~310 | ~310 | Shift analysis (H3) |

C1 tickets never enter train, validation or calibration. The locked test contains a C1
slice so it is "sampled across all four types" (§11.5), and the H3 comparison uses test
C1 plus unseen.

Assignment is greedy within strata of (type, department), largest groups first, so each
split keeps the overall mix. It is deterministic for a seed (default 2026).

## Manifest file and hashes

`data/benchmark/splits_v<N>.json` holds the tickets file path, its SHA-256, the seed, the
counts and the full `ticket_id -> split` map. `check_manifest` rejects:

- a leakage group spanning two splits;
- a C1 ticket outside test or unseen;
- a non-C1 ticket in unseen;
- a ticket without a split.

At the Week 3 freeze, the hashes of the tickets file and the manifest are recorded in
`docs/prereg.md`, and the locked test is read only through `ai/evaluation`.

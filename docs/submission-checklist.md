# Submission checklist (Week 12)

- Owner: Aashritha. Roadmap Week 12 exit gate: "checklist signed by all three; two days
  of buffer left unused for emergencies".
- Status legend: ✅ done · ⏳ in progress · ❌ not started · 👤 needs people.
- Updated 2026-10-30. Each line names the evidence an examiner can open.

## System

| Item | Status | Evidence |
|---|---|---|
| End-to-end system with three roles and a gated pipeline | ✅ | `README.md`, `docs/report/03-system-design.md` |
| Three lanes live (fast, assisted, escalate), fail-closed | ✅ (fast lane closed until thresholds certify one) | `ai/gate/service.py`, `docs/report/06-confidence-engine.md` |
| CI green on `main` | ✅ | GitHub Actions |
| Fresh clone reproduces every development table | ✅ checked 2026-10-30: no file changed | `pip install -r ai/requirements-reproduce.txt`, then `python ai/evaluation/reproduce.py --offline` |
| Fresh clone runs the full system in under 15 minutes | ⏳ | To be timed once the Docker build completes |
| Code freeze announced | ❌ | Roadmap: Wednesday of Week 12 |
| Tag `v1.0` | ❌ | After the locked test and the final report |

## Research

| Item | Status | Evidence |
|---|---|---|
| Benchmark frozen with hashes; locked test sealed | ✅ | `data/benchmark/FREEZE_v1.json`, `data/annotation/locked_test_seal.json` |
| Pre-registration and amendment log | ✅ | `docs/prereg.md` |
| Human labels (600 drafts, 150 double-labelled) | 👤 0 of 600 | Annotation tool `/annotate` |
| Groundedness audit | ✅ all three members, 136 claims | `docs/audit/`, `docs/results/audit-v1.json` |
| Rubric pilot labels | 👤 Rishikesh done; Aashritha and Shivaganesh pending | `docs/pilot/` |
| Locked-test evaluation, exactly once | 👤 waits for human labels | `ai/evaluation/locked_eval.py --final` |
| A second member reproduces the headline numbers | 👤 after the locked test | |
| Baselines B0 to B7 with intervals, ablations, shift study | ✅ (development numbers) | `docs/results/` |
| Red team through the full pipeline | ✅ 0 of 40 | `docs/results/redteam-v3-pipeline.json` |
| User study, 6 to 8 participants | 👤 tool ready, sessions pending | `docs/study/user-study/README.md` |

## Documents

| Item | Status | Evidence |
|---|---|---|
| Report draft v1, all chapters | ✅ | `docs/report/` |
| Final report (results, discussion, study filled in) | ⏳ | waits for labels and the study |
| Datasheet | ✅ | `docs/datasheet.md` |
| Model card | ✅ | `docs/model-card.md` |
| Benchmark release package | ✅ (licence to be decided) | `python ai/benchmark/release.py` |
| Logbooks weeks 1 to 8 | ✅ | `docs/logbook/` |
| Logbooks weeks 9 to 12 | ❌ | |
| Licence for code and data | ❌ | needs the authors' (and institution's) decision |
| Third-party model and data licences recorded | ✅ (Llama 3.1 condition to check) | `docs/third-party-licences.md` |
| No credentials or personal data in the repository | ✅ | `docs/third-party-licences.md`, gitleaks in CI |
| Submission commit recorded | ❌ | tag when the paper is submitted |

## Presentation

| Item | Status | Evidence |
|---|---|---|
| Demo storyboard | ✅ | `docs/demo/storyboard.md` |
| Slides | ⏳ | |
| Three-minute recorded demo video | 👤 | |
| Two full rehearsals | 👤 | |
| Live demonstration to the mentor | 👤 | |

## Sign-off

By signing, each member confirms they have read the final report, that every claim in it
matches what was built and measured, and that no result was tuned on the locked test.

| Member | Signature | Date |
|---|---|---|
| Rishikesh | | |
| Aashritha Reddy | | |
| Shivaganesh | | |

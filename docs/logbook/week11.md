# Logbook — Week 11 (28 Dec 2026 to 3 Jan 2027): full-system testing and refinement

## Exit gate

| Condition | Status | Evidence |
|---|---|---|
| Week 10 bugs resolved | **green** | [bug-bash-week11.md](../bug-bash-week11.md): 5 found, 5 fixed; backend 178 and AI 159 tests passing at the time |
| Latency measured | **green** | [latency-cost.md](../latency-cost.md) |
| Test suite in place | **green** | CI: lint, frontend, backend, AI unit tests with a 70% coverage floor |
| Evaluation results finalised | **amber** | Rules fixed before the locked test (B3 added, H2 refit per resplit, H3 exposure); results wait for Week 12 |

## Rishikesh
- Security: dependencies upgraded past known vulnerabilities (pyjwt, pypdf, pillow, urllib3,
  certifi, setuptools; vite via npm audit); a weak JWT secret is refused outside development.
- Bug bash; ticket subjects are links for keyboard users; V1 threshold control removed;
  model health counts only gate-scored tickets.
- Tickets the pipeline cannot finish or route are escalated instead of stranded; lifecycle doc rewritten.
- Report draft v1: system design, retrieval and generation, security, appendices; data-model diagram.
- Package versions pinned so the committed results reproduce byte for byte; third-party licences recorded.
- Groundedness audit scored against both claim checkers.

## Aashritha
- User-study tool: participant role, fixed-lane tasks, server-side timing, KB search, `/study`
  screen, setup and blind-grading export.
- Report: introduction and user-experience chapters; submission checklist.
- Groundedness audit labels (53 claims).

## Shivaganesh
- H4 user-study analysis; model card; benchmark release package with checksums; datasheet.
- Before the locked test was read: B3 added to the evaluation, H2 refits calibration inside
  each resplit, H3 reports class counts, e-AURC and exposure (each logged in [prereg.md](../prereg.md)).
- Groundedness audit labels (43 claims).

## Findings
- **NLI accepts too much.** In the three-member groundedness audit the NLI checker passed
  most claims the members rejected; the paper reports it as a limitation.

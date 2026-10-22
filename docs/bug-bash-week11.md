# Bug bash (Week 11)

- Owner: Rishikesh. Roadmap Week 11: "bug bash; fix critical issues only".
- Date: 2026-10-22, on `main` after the Week 11 merges.
- Method: a headless browser logged in as each demo role and opened every main page,
  recording console errors, failed requests and error messages; then targeted checks.
  Backend 178 tests and AI 159 tests passed before and after.

## Found and fixed

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | Ticket tables for all three roles (engineer queue, admin tickets, end-user home) | Rows opened a ticket on mouse click only; a keyboard user could not open any ticket | Each subject is a real link; Tab then Enter opens the ticket (checked for all three roles) |
| 2 | `/tickets` API | A `participant` (study) account could list tickets | Participants are blocked like annotators (found by the study tests) |
| 3 | Dependencies, JWT secret | See the Week 11 security checks in [report chapter 8](report/08-security-and-responsible-ai.md) | Upgraded; weak secret refused outside development |

## Found, not fixed (needs a decision)

| # | Where | Problem | Why not fixed now |
|---|---|---|---|
| 4 | Admin → Departments | Still shows the V1 per-department confidence threshold ("0–55% goes to your Approvals queue"), which no longer decides anything: lanes come from the certified gate thresholds | Part of the V1 cleanup list awaiting the owner's approval |
| 5 | Admin → Model health | Shows the V1 confidence model report (121 labels, mostly synthetic bootstrap), not `confidence-v1` | Same |

## Open, not reproduced reliably

| # | Where | What happens | What is known |
|---|---|---|---|
| 6 | Admin pages, local development | About 1 page load in 20 in the headless browser, one or two requests end with `net::ERR_FAILED` and the page shows "Could not load …"; a reload fixes it | The server logs every one of those requests as `200 OK`; the same requests made 15 times from inside the page all succeeded; a second full run was clean. Seen only with the local dev servers, not yet checked against the Docker build or a normal browser |

## Not bugs

- An earlier run showed "Could not load" on four admin pages every time. Cause: a stale
  Vite dev server whose `node_modules` were replaced by `npm audit fix` while it ran. A
  fresh build loads all pages.

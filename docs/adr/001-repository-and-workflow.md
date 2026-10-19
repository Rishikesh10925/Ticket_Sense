# ADR 001: Repository layout and team workflow

- Status: accepted
- Date: 2026-10-19
- Owner: Rishikesh

## Context

Blueprint Appendix B proposes `apps/api`, `apps/web`, `packages/*`, `data`, `docs`,
`infra`. The repository already has a working layout (`backend/`, `frontend/`, `ai/`,
`db/`, `data/`, `docs/`), wired into Docker, Render, Vercel, Alembic and dozens of
relative-path imports. The team also never uses pull requests.

## Decision

Keep the existing top-level layout and map it to Appendix B instead of moving files:

| Appendix B | This repository |
|---|---|
| `apps/api` | `backend/` (FastAPI, models, routers, tests) |
| `apps/web` | `frontend/` (React + TypeScript + Vite) |
| `packages/pipeline` | `ai/graph/`, `ai/generation/` |
| `packages/retrieval` | `ai/embeddings/` (renamed in Week 4 when hybrid retrieval lands) |
| `packages/grounding` | `ai/grounding/` (Week 5) |
| `packages/confidence` | `ai/confidence/` |
| `packages/evaluation` | `ai/evaluation/` |
| `data/kb` | `data/kb/` (moved from `db/seed/knowledge_base/` in Week 1) |
| `data/benchmark`, `data/redteam` | same |
| `infra/` | `docker-compose.yml`, Dockerfiles, `.github/workflows/` |
| `Makefile` | `Makefile` → `tasks.py` (works on Windows without make) |

Workflow:

- One short-lived branch per member per week, `week<N>-<member>-<topic>`, merged
  directly into `main` at the end of the week. No pull requests.
- Because nothing gates a merge, CI runs on every push to every branch, and a branch is
  merged only when its CI is green. `main` must always be green.
- Commit messages are short and lowercase. Each commit is authored by the member who
  owns that work.
- Milestone tags: v0.1 (W2), v0.2 (W4), v0.3 (W6), v0.4 (W8), v0.9 (W10), v1.0 (W12).

## Consequences

- No mass rename, so deployment and imports keep working.
- Without branch protection, the "CI green before merge" rule is a team habit rather than
  something GitHub enforces. The weekly merge checklist in the logbook records it.

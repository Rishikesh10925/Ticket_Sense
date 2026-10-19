# Definition of done

Agreed in the Week 1 design session (Blueprint V2 §21.2, Roadmap §4). A task is done only when:

1. **Merged and green.** The work is on `main` and CI is green for that commit. There are
   no pull requests in this team, so the author checks `gh run list` before merging the
   weekly branch, and the logbook records it.
2. **Tested.** New logic has tests: unit tests in `ai/tests/` (no database) or API tests
   in `backend/tests/` (Postgres). Evaluation and pipeline code target 70% line coverage.
3. **Reproducible.** Any number in a document comes from a command another member can
   run (`python tasks.py <task>` or a script path), with fixed seeds and the data hash
   recorded. Every ML result is reproduced by a second member before it is reported.
4. **Documented.** The relevant doc or ADR is updated, and the member's weekly logbook
   entry links to the commit or experiment id.
5. **Demonstrable.** The week's mentor-facing evidence exists: a screenshot, a table or a
   live demo path.

## Working rules (Roadmap §4.1)

- At most two open items per person.
- A task slipping two days is raised at once in the team chat.
- A milestone slipping three days triggers the cut list (Roadmap §7).
- New ideas go to the parking lot in the logbook, reviewed at the Friday retrospective.
- Every major choice gets a short ADR in `docs/adr/`.

## Commits and branches

- Branches: `week<N>-<member>-<topic>`, merged into `main` at the end of the week (ADR 001).
- Commit messages: short and lowercase, authored by the owner of the work.
- Tags at milestones: v0.1 (W2), v0.2 (W4), v0.3 (W6), v0.4 (W8), v0.9 (W10), v1.0 (W12).

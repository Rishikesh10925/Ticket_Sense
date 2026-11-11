# 10. Appendices

*Owner: Rishikesh. Draft v1.*

## A. Labelling rubric

[docs/labelling-rubric.md](../labelling-rubric.md), with the [reviewer guide](../study/reviewer-guide.md).

## B. Schemas

- API: [docs/openapi.json](../openapi.json) (regenerated with `python tasks.py openapi`).
- Database: `backend/app/models/` and `db/migrations/versions/` (0001 to 0023).
- Draft JSON: `ai/generation/drafting.py`.

## C. Reproduction

```bash
git clone <repository> && cd Tickesense
uv venv --python 3.12 .venv
uv pip install numpy scipy pandas scikit-learn xgboost pyyaml
python ai/evaluation/reproduce.py --offline      # every development table and figure
```

The full system (database, models, pipeline) is described in the root README. The locked
test was evaluated once, on 11 November 2026, with
`python ai/evaluation/locked_eval.py --final --labels judge` (against LLM-judge labels; see
the 2026-11-11 amendment).

## D. Pre-registration and amendments

[docs/prereg.md](../prereg.md).

## E. References

**To be filled** from the blueprint reference list.

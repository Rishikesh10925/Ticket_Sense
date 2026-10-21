"""Regenerate every evaluation table from the frozen benchmark and the stored drafts,
signals and labels (Roadmap Week 8 deliverable: "confidence model v1 and calibration
reproducible by one command"; exit gate: "second member reproduces the model results").

    python tasks.py reproduce                  # judge labels (development)
    python ai/evaluation/reproduce.py --labels human

Steps, each a separate script so any one can be rerun alone:

    1. verify the benchmark freeze and the locked-test seal
    2. retrieval metrics (docs/results/retrieval-v1.json)
    3. baselines B0 to B7 (docs/results/baselines-v1-<labels>.json)
    4. confidence model, calibration, lane thresholds (docs/results/confidence-v1-<labels>.json)
    5. feature-group ablations (docs/results/ablations-v1-<labels>.json)
    6. label agreement (docs/results/agreement-v1.json)
    7. locked-evaluation rehearsal on validation, with figures (judge labels only;
       docs/results/locked-rehearsal-judge.*). The one real locked-test run is never part
       of this command: `python ai/evaluation/locked_eval.py --final` (Week 10).

It reads the database the pipeline wrote (drafts, signals, labels) and never the locked
test split. The numbers are deterministic: same inputs, same tables.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))


def steps(labels: str) -> list[tuple[str, list[str]]]:
    return [
        ("retrieval", ["ai/retrieval/evaluate.py"]),
        ("baselines", ["ai/signals/report_baselines.py", "--labels", labels]),
        ("confidence model", ["ai/confidence_model/train.py", "--labels", labels]),
        ("ablations", ["ai/confidence_model/ablate.py", "--labels", labels]),
        ("agreement", ["ai/evaluation/agreement.py"]),
    ] + ([("locked rehearsal", ["ai/evaluation/locked_eval.py", "--rehearse"])] if labels == "judge" else [])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", choices=["judge", "human"], default="judge")
    parser.add_argument("--skip", nargs="*", default=[], help="step names to skip, e.g. retrieval")
    args = parser.parse_args()

    from confidence_model.dataset import verify_inputs

    verify_inputs("v1")
    print("1. freeze and locked-test seal verified")
    for n, (name, cmd) in enumerate(steps(args.labels), start=2):
        if name in args.skip:
            print(f"{n}. {name}: skipped")
            continue
        started = time.perf_counter()
        result = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"{n}. {name} FAILED\n{result.stderr[-2000:]}")
        print(f"{n}. {name}: done in {time.perf_counter() - started:.0f} s")
    print("All tables regenerated under docs/results/.")


if __name__ == "__main__":
    main()

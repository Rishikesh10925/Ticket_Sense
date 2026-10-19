from typing import Literal

# One list for outside reviewers (annotation tool) and engineers (workbench), so the
# two kinds of feedback can be compared code by code (docs/labelling-rubric.md).
ReasonCode = Literal[
    "wrong_source", "outdated_source", "missing_step", "invented_step",
    "did_not_address_question", "tone", "formatting", "other",
]

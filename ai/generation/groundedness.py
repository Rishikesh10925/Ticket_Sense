"""Groundedness check: verify every citation marker in a generated draft maps to an
actual retrieved evidence item, and flag any substantive line that has no citation at
all. See docs/draft-generation.md.
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "embeddings"))

from retrieve import EvidenceResult  # noqa: E402

_CITATION_RE = re.compile(r"\[(\d+)\]")


@dataclass
class GroundednessReport:
    total_citations: int
    grounded_citations: int
    ungrounded_markers: list[int] = field(default_factory=list)
    uncited_lines: list[str] = field(default_factory=list)

    @property
    def is_fully_grounded(self) -> bool:
        return not self.ungrounded_markers and not self.uncited_lines


def check_groundedness(draft: str, evidence: list[EvidenceResult]) -> GroundednessReport:
    markers = [int(m) for m in _CITATION_RE.findall(draft)]
    grounded = [m for m in markers if 1 <= m <= len(evidence)]
    ungrounded = sorted({m for m in markers if not (1 <= m <= len(evidence))})

    uncited_lines = [
        line.strip()
        for line in draft.splitlines()
        if line.strip().startswith("-") and not _CITATION_RE.search(line)
    ]

    return GroundednessReport(
        total_citations=len(markers),
        grounded_citations=len(grounded),
        ungrounded_markers=ungrounded,
        uncited_lines=uncited_lines,
    )

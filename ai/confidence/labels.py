"""Turns a reviewer's Feedback row into a training label.

Implements the accept/edit/reject/escalate -> success/failure mapping
docs/confidence-labelling-guide.md proposed in Week 3 as a *plan*, before any real
`feedback` rows existed. Week 9 is when the reviewer UI starts actually populating that
table (see docs/langgraph-pipeline.md's "Reviewing a gated ticket"), so this is where
the plan becomes code.
"""

import difflib

# The account seed_synthetic_confidence_data.py logs bootstrapped Week 8 feedback
# under (see backend/app/scripts/seed_synthetic_confidence_data.py) — rows attributed
# to it are not a real reviewer's judgment and must never be counted as real signal.
SYNTHETIC_REVIEWER_EMAIL = "synthetic-reviewer@ticketsense.local"

# The guide's recommended starting point for "minor" vs. "heavy" edit: <15% of the
# text changed = minor. Picked because it needed no UI/schema changes, not because it's
# been validated against a manual spot-check yet — see the guide's "Open question"
# section. Revisit once enough real edits exist to calibrate against reality.
MINOR_EDIT_MAX_CHANGE_RATIO = 0.15


def edit_change_ratio(original: str, edited: str) -> float:
    """Fraction of `original` that changed to produce `edited`.

    difflib's SequenceMatcher ratio (edit-distance-ratio's cheapest form, per the
    guide) rather than true Levenshtein distance or a semantic-similarity model —
    the guide's explicit recommendation for a first pass with no dependency cost.
    """
    similarity = difflib.SequenceMatcher(None, original, edited).ratio()
    return 1.0 - similarity


def label_from_feedback(action: str, ai_draft_reply: str | None, edited_reply: str | None) -> bool | None:
    """Maps one `feedback` row to a training label: True (success), False (failure),
    or None (excluded — nothing to learn from this row).

    See docs/confidence-labelling-guide.md's mapping table for the rationale behind
    each case, including the `escalate` case: the guide originally excluded escalation
    from training because no draft existed to judge, but noted that a reviewer
    escalating a ticket that *did* have a draft should be labelled like a reject —
    that flow now exists (Week 9's reviewer-initiated escalate), so it's handled here.
    """
    if action == "accept":
        return True
    if action == "reject":
        return False
    if action == "edit":
        if ai_draft_reply is None or edited_reply is None:
            return False
        return edit_change_ratio(ai_draft_reply, edited_reply) <= MINOR_EDIT_MAX_CHANGE_RATIO
    if action == "escalate":
        return False if ai_draft_reply is not None else None
    return None

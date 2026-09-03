import sys
from pathlib import Path

AI_CONFIDENCE_DIR = Path(__file__).resolve().parents[2] / "ai" / "confidence"
sys.path.insert(0, str(AI_CONFIDENCE_DIR))

from labels import edit_change_ratio, label_from_feedback  # noqa: E402

DRAFT = "Please restart the VPN client, then reconnect using the gateway address on file."


def test_accept_is_success():
    assert label_from_feedback("accept", DRAFT, None) is True


def test_reject_is_failure():
    assert label_from_feedback("reject", DRAFT, None) is False


def test_minor_edit_is_success():
    edited = "Please restart the VPN client, then reconnect using the gateway address we have on file."
    assert label_from_feedback("edit", DRAFT, edited) is True


def test_heavy_edit_is_failure():
    edited = "Escalating to networking — this needs a firmware check on the office router."
    assert label_from_feedback("edit", DRAFT, edited) is False


def test_edit_without_a_draft_is_treated_as_failure():
    assert label_from_feedback("edit", None, "some replacement text") is False


def test_escalate_after_a_draft_is_failure():
    assert label_from_feedback("escalate", DRAFT, None) is False


def test_escalate_without_a_draft_is_excluded():
    assert label_from_feedback("escalate", None, None) is None


def test_unknown_action_is_excluded():
    assert label_from_feedback("bogus", DRAFT, None) is None


def test_edit_change_ratio_is_zero_for_identical_text():
    assert edit_change_ratio(DRAFT, DRAFT) == 0.0


def test_edit_change_ratio_is_high_for_a_full_rewrite():
    assert edit_change_ratio(DRAFT, "Completely different content with nothing shared.") > 0.5

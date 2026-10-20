from confidence_model.ablate import EXTRA, GROUPS, columns_without
from confidence_model.model import FEATURES


def test_every_feature_belongs_to_exactly_one_group():
    owners = {f: [g for g, prefix in GROUPS.items() if f.startswith(prefix)] for f in FEATURES}
    assert all(len(v) == 1 for v in owners.values()), {f: v for f, v in owners.items() if len(v) != 1}


def test_dropping_the_probe_removes_only_its_two_columns():
    keep = columns_without(set(EXTRA["cross-department probe"]))
    assert len(keep) == len(FEATURES) - 2
    assert all(FEATURES[i] not in EXTRA["cross-department probe"] for i in keep)

"""The benchmark release is complete, reproducible and checksummed (Week 12)."""

import hashlib
import zipfile

from benchmark import release


def test_release_is_complete_and_reproducible(tmp_path):
    first = release.build("v1", tmp_path / "a")
    second = release.build("v1", tmp_path / "b")
    assert first.read_bytes() == second.read_bytes()  # byte-for-byte reproducible

    with zipfile.ZipFile(first) as z:
        names = z.namelist()
        prefix = "ticketsense-benchmark-v1/"
        for needed in ("README.md", "SHA256SUMS", "benchmark/benchmark_v1.jsonl", "benchmark/splits_v1.json",
                       "benchmark/FREEZE_v1.json", "docs/datasheet.md", "redteam/injection_v1.jsonl"):
            assert prefix + needed in names
        assert sum(n.startswith(prefix + "kb/") for n in names) == 120
        sums = z.read(prefix + "SHA256SUMS").decode().splitlines()
        assert len(sums) == len(names) - 1
        for line in sums:
            digest, name = line.split("  ")
            assert hashlib.sha256(z.read(prefix + name)).hexdigest() == digest
        assert not any("label" in n and n.endswith((".csv", ".jsonl")) for n in names)  # no labels shipped

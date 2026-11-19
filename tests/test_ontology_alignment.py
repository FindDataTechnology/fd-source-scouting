"""`ontology_alignment` must resolve to real concept families.

The field answers "which part of the ontology does this source fill?". An
invented id would make the coverage statistic count a source as covering
something the ontology does not have — a false green that is worse than no
alignment at all.

Absent alignment is legal ("not declared"): such a source simply does not enter
the coverage statistic. That distinction is the point of the field.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_ontology_alignment as ck  # noqa: E402


@pytest.fixture(scope="module")
def vocab():
    return ck._load_protocol_concepts()


def _cand(**over) -> dict:
    base = {"candidates": [{"name": "源 A", **over}]}
    return base


def test_real_concept_families_pass(vocab):
    allowed, version = vocab
    sample = sorted(allowed)[:2]
    problems = ck.check(
        _cand(ontology_alignment=sample, protocol_version=version), allowed, version
    )
    assert problems == []


def test_absent_alignment_is_legal(vocab):
    """No declaration is a state, not an error — the source just is not counted."""
    allowed, version = vocab
    assert ck.check(_cand(), allowed, version) == []


def test_invented_concept_family_is_refused(vocab):
    allowed, version = vocab
    problems = ck.check(
        _cand(ontology_alignment=["NotAConcept"], protocol_version=version),
        allowed, version,
    )
    assert problems and "NotAConcept" in problems[0]


def test_alignment_without_protocol_version_is_refused(vocab):
    """Without a version, a later vocabulary release cannot be reconciled."""
    allowed, version = vocab
    problems = ck.check(_cand(ontology_alignment=sorted(allowed)[:1]), allowed, version)
    assert any("protocol_version" in p for p in problems)


def test_the_checker_can_fail_on_a_real_file(tmp_path, vocab):
    """A gate that has never been red is not a gate."""
    allowed, version = vocab
    bad = tmp_path / "cand.json"
    bad.write_text(json.dumps(_cand(
        ontology_alignment=["DefinitelyFake"], protocol_version=version
    ), ensure_ascii=False), encoding="utf-8")
    assert ck.main(["--candidates", str(bad), "--quiet"]) == 1


def test_shipped_data_has_no_broken_alignment(vocab):
    """The real candidates file must stay clean as alignment gets filled in."""
    allowed, version = vocab
    cand = json.loads((ROOT / "candidates.json").read_text(encoding="utf-8"))
    assert ck.check(cand, allowed, version) == []

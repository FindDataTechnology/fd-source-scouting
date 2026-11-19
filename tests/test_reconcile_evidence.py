"""The reconciliation sweep must report, never repair.

Repairing means re-running a probe against the outside world — a deliberate act.
A sweep that silently "fixed" things would re-request external endpoints on a
schedule, which is exactly the cost the drift check exists to avoid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import reconcile_evidence as rec  # noqa: E402


def trap(tid: str, **over) -> dict:
    return {"id": tid, **over}


def test_agreeing_sides_are_not_reported():
    traps = [trap("a", last_probe={"ok": True})]
    ontology = {"a": {"executor_tests": {"ok": True, "evidence": "e"}}}
    assert rec.sweep(traps, ontology) == []


def test_archive_pass_without_ontology_evidence_is_reported():
    """The probe ran but the evidence never landed — re-run, do not trust it."""
    traps = [trap("b", last_probe={"ok": True})]
    rows = rec.sweep(traps, {})
    assert len(rows) == 1
    assert "本体侧没有证据" in rows[0]["reason"]


def test_opposite_conclusions_are_reported():
    traps = [trap("c", last_probe={"ok": True})]
    ontology = {"c": {"executor_tests": {"ok": False, "evidence": "e"}}}
    rows = rec.sweep(traps, ontology)
    assert rows and "相反" in rows[0]["reason"]


def test_both_silent_is_not_a_conflict():
    assert rec.sweep([trap("d")], {}) == []


def test_traps_without_id_are_skipped():
    assert rec.sweep([{"no_id": True}], {}) == []


def test_conclusion_field_is_read_when_no_probe_record():
    """Older traps carry a textual conclusion, not a probe record."""
    traps = [trap("e", conclusion="ok")]
    ontology = {"e": {"executor_tests": {"ok": False, "evidence": "x"}}}
    assert rec.sweep(traps, ontology)


def test_the_sweep_can_fail(tmp_path):
    """A sweep that has never been red is not a sweep."""
    src = tmp_path / "traps.json"
    src.write_text(json.dumps({"traps": [trap("f", last_probe={"ok": True})]}))
    onto = tmp_path / "onto.json"
    onto.write_text(json.dumps({}))
    assert rec.main(["--traps", str(src), "--ontology", str(onto), "--quiet"]) == 1


def test_clean_sweep_exits_zero(tmp_path):
    src = tmp_path / "traps.json"
    src.write_text(json.dumps({"traps": [trap("g", last_probe={"ok": False})]}))
    onto = tmp_path / "onto.json"
    onto.write_text(json.dumps({"g": {"executor_tests": {"ok": False, "evidence": "e"}}}))
    assert rec.main(["--traps", str(src), "--ontology", str(onto), "--quiet"]) == 0

"""One probe result → one record of reachability.

The bug this prevents is a specific one: the drift archive and the ontology's
crosswalk each maintained their own idea of "is this source reachable", so
"the archive says it works" and "the ontology says it is broken" could both be
true and nothing would notice.

Two invariants matter most:

- **`executor_tests` is all a probe can clear.** A probe proves the source
  answers as declared; it proves nothing about the provider directory
  (`catalog`) or human acceptance (`live`). Letting a green probe imply those
  would make "probe passed" read as "safe for production".
- **a passed test without evidence is refused.** An "ok" nobody can check is
  what the whole seam exists to prevent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import probe_to_connectivity as p2c  # noqa: E402


def test_passing_probe_marks_executor_tests_ok():
    state = p2c.connectivity_state(
        {"kind": "ok", "status": "ok", "reason": ""}, evidence_ref="evidence/r1.json"
    )
    assert state["ok"] is True
    assert state["evidence"] == "evidence/r1.json"
    assert state["probe_kind"] == "ok"


def test_caliber_mismatch_is_a_failed_executor_test():
    """HTTP 200 with the wrong shape is not a pass — the executor does not work."""
    state = p2c.connectivity_state(
        {"kind": "caliber_mismatch", "status": "ok", "reason": "缺少 tradeDate"},
        evidence_ref="evidence/r2.json",
    )
    assert state["ok"] is False
    assert "tradeDate" in state["reason"]


def test_failure_keeps_the_probe_classification():
    state = p2c.connectivity_state(
        {"kind": "auth_required", "status": "error", "reason": "401"},
        evidence_ref="e.json",
    )
    assert state["ok"] is False
    assert state["probe_kind"] == "auth_required"


def test_evidence_ref_is_always_required():
    """A pass with no pointer is exactly the 'ok nobody can check' case."""
    state = p2c.connectivity_state({"kind": "ok", "status": "ok"}, evidence_ref="x")
    assert state["evidence"] == "x"


def test_merge_touches_only_executor_tests():
    """catalog and live belong to other authorities."""
    existing = {
        "catalog": {"ok": True, "evidence": "catalog/apps/x.json"},
        "live": {"ok": False, "evidence": None},
    }
    merged = p2c.merge_into_connectivity(
        existing, executor_state={"ok": True, "evidence": "e.json"}
    )
    assert merged["catalog"] == existing["catalog"]
    assert merged["live"] == existing["live"]
    assert merged["executor_tests"]["ok"] is True


def test_merge_into_nothing_creates_only_executor_tests():
    merged = p2c.merge_into_connectivity(None, executor_state={"ok": True, "evidence": "e"})
    assert set(merged) == {"executor_tests"}


# ------------------------------------------------------------ staleness


def test_agreement_is_not_stale():
    assert p2c.is_stale_pair({"ok": True}, {"executor_tests": {"ok": True}}) is None


def test_both_silent_is_not_a_conflict():
    assert p2c.is_stale_pair({}, None) is None


def test_opposite_conclusions_are_flagged_both_ways():
    msg = p2c.is_stale_pair({"ok": True}, {"executor_tests": {"ok": False}})
    assert msg and "相反" in msg
    msg2 = p2c.is_stale_pair({"ok": False}, {"executor_tests": {"ok": True}})
    assert msg2 and "相反" in msg2


def test_one_sided_record_is_flagged():
    assert p2c.is_stale_pair({"ok": True}, None)
    assert p2c.is_stale_pair({}, {"executor_tests": {"ok": True}})

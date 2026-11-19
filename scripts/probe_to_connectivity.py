"""One probe result feeds both the drift report and the crosswalk evidence.

The rule this exists to enforce: **there is exactly one record of "is this source
reachable"**. Before it, `regression-traps.json` said one thing and the platform's
crosswalk `connectivity` said another, and nothing noticed when they disagreed —
which meant "the archive says it works" and "the ontology says it is broken"
could both be true at the same time.

What this module does NOT do: it does not run the probe, it does not decide
whether a source is dead, and it does not write to the database. It translates a
probe verdict into the shape the seam expects, so the translation has one
definition and a unit test.

On the semantic floor: `executor_tests` is the state a probe can actually clear.
`catalog` is the provider-directory claim and `live` is a human-accepted
acceptance record; a probe passing proves neither. Conflating them would let
"probe is green" be read as "safe to production", which is exactly what the
three-state discipline exists to prevent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

#: The probe verdict kinds that mean "the source answered as declared".
#:
#: `ok` is the obvious one. The others are deliberately NOT included: a
#: `caliber_mismatch` means the response shape does not match the declaration,
#: which is a failed executor test even though the HTTP call succeeded.
PASSING_KINDS = ("ok",)

#: Probe failure kinds → the phrase recorded in the evidence block. The probe's
#: own four-way classification (`source-probe` spec) is preserved verbatim so a
#: later reader can tell "network" from "auth" without re-running anything.
FAILURE_CLASSES = (
    "unreachable",
    "auth_required",
    "caliber_mismatch",
    "upstream_error",
)


def connectivity_state(result: dict, *, evidence_ref: str) -> dict:
    """Translate one probe result into an `executor_tests` state block.

    `evidence_ref` is required in both directions: a passing test with no
    evidence pointer is precisely the "ok nobody can check" the seam refuses, and
    a failure without an evidence pointer cannot be triaged later.
    """
    kind = (result or {}).get("kind") or ""
    reason = (result or {}).get("reason") or ""
    status = (result or {}).get("status")

    if kind in PASSING_KINDS:
        return {
            "ok": True,
            "evidence": evidence_ref,
            "at": _now(),
            "probe_kind": kind,
        }
    return {
        "ok": False,
        "evidence": evidence_ref,
        "at": _now(),
        "probe_kind": kind or "unknown",
        "reason": reason or f"probe status {status!r}",
    }


def merge_into_connectivity(
    existing: Optional[dict], *, executor_state: dict
) -> dict:
    """Merge one `executor_tests` result into an existing connectivity block.

    Only `executor_tests` is touched. `catalog` and `live` belong to other
    authorities (the provider directory and a human acceptance), and a probe has
    no standing to overwrite either.
    """
    block = dict(existing or {})
    block["executor_tests"] = executor_state
    return block


def is_stale_pair(archive: dict, connectivity: Optional[dict]) -> Optional[str]:
    """Does the archive and the seam disagree about `executor_tests`?

    Returns a human-readable description of the disagreement, or ``None`` when
    they agree. Agreement includes "neither says anything" — silence on both
    sides is not a conflict, it is an unprobed source.
    """
    archive_ok = archive.get("ok")
    seam = (connectivity or {}).get("executor_tests") or {}
    seam_ok = seam.get("ok")

    if archive_ok is None and seam_ok is None:
        return None
    if archive_ok is None:
        return "本体侧有证据、接入档案没有对应记录"
    if seam_ok is None:
        return "接入档案有探测结论、本体侧没有证据"
    if bool(archive_ok) != bool(seam_ok):
        return (
            f"两侧结论相反：接入档案 ok={archive_ok}，"
            f"本体 executor_tests ok={seam_ok}"
        )
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

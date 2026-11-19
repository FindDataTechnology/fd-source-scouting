#!/usr/bin/env python3
"""Find sources where the drift archive and the ontology disagree.

`is_stale_pair` in `probe_to_connectivity` answers "do these two records
conflict?" for one source. This script is the sweep: it walks every trap whose
archive claims a verdict and reports the ones the ontology does not back.

Two failure shapes matter, and they need different fixes:

- **archive says pass, ontology has nothing** → the probe ran but the evidence
  never landed (the write failed, or the source was probed before the seam
  existed). Re-run the probe; do not trust the archive alone.
- **both say something but disagree** → one of them is stale. Which one is a
  judgement call, so this script reports rather than repairs.

Read-only by design: it prints a worklist. Repairing means re-running a probe
against the outside world, which is a deliberate act, not a sweep step.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from probe_to_connectivity import is_stale_pair  # noqa: E402


def load_traps(path: Path) -> list[dict]:
    body = json.loads(path.read_text(encoding="utf-8"))
    return body.get("traps", [])


def archive_verdict(trap: dict) -> dict:
    """What the archive currently claims about this trap, if anything.

    The trap file records the *conclusion* (`conclusion` / `if_changed`) plus the
    last probe outcome where one was captured. Absence of both means the archive
    says nothing, which is not a conflict.
    """
    last = trap.get("last_probe") or {}
    if "ok" in last:
        return {"ok": bool(last["ok"])}
    verdict = trap.get("verdict") or {}
    kind = verdict.get("kind") or trap.get("conclusion")
    if kind == "ok":
        return {"ok": True}
    if kind:
        return {"ok": False}
    return {}


def sweep(traps: list[dict], ontology: dict[str, dict]) -> list[dict]:
    """Rows that need attention, each with a human-readable reason."""
    out = []
    for trap in traps:
        tid = trap.get("id")
        if not tid:
            continue
        archive = archive_verdict(trap)
        seam = ontology.get(tid)
        reason = is_stale_pair(archive, seam)
        if reason:
            out.append({"id": tid, "reason": reason,
                        "archive": archive, "ontology": seam})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--traps", default=str(ROOT / "regression-traps.json"))
    ap.add_argument("--ontology", default=None,
                    help="JSON: {trap_id: {executor_tests: {ok, evidence}}}；"
                         "省略则视为本体侧不可读")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    traps = load_traps(Path(args.traps))
    if args.ontology:
        ontology = json.loads(Path(args.ontology).read_text(encoding="utf-8"))
    else:
        ontology = {}

    rows = sweep(traps, ontology)
    if not args.quiet:
        print(f"{len(traps)} 条陷阱，{len(rows)} 条两侧不一致或单侧缺失")

    if not rows:
        if not args.quiet:
            print("OK: 接口档案与本体证据一致")
        return 0

    for r in rows:
        print(f"  {r['id']}: {r['reason']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

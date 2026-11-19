#!/usr/bin/env python3
"""Validate `ontology_alignment` against the protocol's concept vocabulary.

The alignment field answers "which part of the ontology does this source fill?".
It must name **real concept families** — an invented id would produce a statistic
that counts a source as covering something the ontology does not have, which is
worse than no alignment at all (see change design D5: an alignment nobody can
resolve is a false green).

Absent alignment is legal and means "not declared" — that source simply does not
enter the coverage statistic. What is *not* legal is an id that looks like it
should resolve but does not.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CANDIDATES = ROOT / "candidates.json"

#: Where the protocol package lives, in order of preference: an explicit env
#: override, then the sibling checkout in this workspace.
PROTOCOL_ENV = "FD_OPEN_DATA_PROTOCOL_DIR"
PROTOCOL_SIBLING = ROOT.parent / "fd-open-data-protocol"


def _load_protocol_concepts() -> tuple[set[str], str]:
    """(concept family ids, vocabulary version). Fails loudly when unavailable."""
    import os

    src = os.environ.get(PROTOCOL_ENV)
    path = Path(src) if src else PROTOCOL_SIBLING
    if not (path / "fd_open_data_protocol" / "vocabulary.py").is_file():
        raise SystemExit(
            f"protocol package not found at {path} — set {PROTOCOL_ENV} or "
            "check out fd-open-data-protocol next to this workspace. Refusing to "
            "validate alignment against nothing."
        )
    sys.path.insert(0, str(path))
    try:
        from fd_open_data_protocol.vocabulary import load_vocabulary
    finally:
        sys.path.pop(0)
    reg = load_vocabulary()
    ids = {e.id for e in reg.entries.get("concept", [])}
    return ids, str(getattr(reg, "version", "unknown"))


def check(candidates: dict, allowed: set[str], version: str) -> list[str]:
    problems: list[str] = []
    for row in candidates.get("candidates", []):
        declared = row.get("ontology_alignment")
        if declared is None:
            continue  # not declared: legal, just not counted
        if not isinstance(declared, list):
            problems.append(f"{row.get('name')!r}: ontology_alignment 必须是数组")
            continue
        unknown = [c for c in declared if c not in allowed]
        if unknown:
            problems.append(
                f"{row.get('name')!r}: 概念族未在协议 {version} 词表内：{unknown}"
                f"（可用示例：{sorted(allowed)[:6]}）"
            )
        if declared and not row.get("protocol_version"):
            problems.append(
                f"{row.get('name')!r}: 声明了对齐但缺 protocol_version —— "
                "没有版本，协议升版后无法判断这条声明按哪份词表读"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", default=str(CANDIDATES))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    cand = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    allowed, version = _load_protocol_concepts()
    problems = check(cand, allowed, version)

    if not args.quiet:
        declared = [
            r for r in cand.get("candidates", [])
            if r.get("ontology_alignment")
        ]
        print(f"协议词表 {version}：{len(allowed)} 个概念族")
        print(f"已声明对齐的候选：{len(declared)} / {len(cand.get('candidates', []))}")

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    if not args.quiet:
        print("OK: 所有对齐声明都能解析到协议词表")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

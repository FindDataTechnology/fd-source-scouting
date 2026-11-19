#!/usr/bin/env python3
"""Check the vertical registry against the real candidate data.

Two assertions, both of which must hold before any normalisation runs:

1. every distinct `vertical` value in `candidates.json` has a home in the
   registry — a value with no home is a classification nobody has decided on;
2. no registry entry is unused — a dead entry is a classification that drifted
   away from the data it describes.

The registry splits one overloaded column into two orthogonal dimensions
(`source_class` for the A–N document sections, `topic` for everything else).
This checker only proves coverage; it does not decide which value means what.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATES = HERE.parent / "candidates.json"
REGISTRY = HERE.parent / "vertical-registry.json"


def load() -> tuple[dict, dict]:
    cand = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return cand, reg


def known(reg: dict) -> tuple[set[str], set[str]]:
    dims = reg["dimensions"]
    classes = set(dims["source_class"]["values"])
    topics = set(dims["topic"]["values"])
    return classes, topics


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    cand, reg = load()
    classes, topics = known(reg)
    single = set(reg["mapping"]["single_letter_to_source_class"])

    used: Counter[str] = Counter()
    for row in cand["candidates"]:
        for v in row.get("vertical") or []:
            used[v] += 1

    homeless_class = sorted(v for v in used if v in single and v not in classes)
    homeless_topic = sorted(
        v for v in used if v not in single and v not in topics
    )
    unused = sorted((classes | topics) - set(used))

    problems = []
    if homeless_class:
        problems.append(
            f"来源类别取值未登记：{homeless_class}（加进 dimensions.source_class.values）"
        )
    if homeless_topic:
        problems.append(
            f"主题取值未登记：{homeless_topic}（加进 dimensions.topic.values）"
        )
    if unused:
        problems.append(
            f"登记项没有任何候选使用：{unused}（是笔误还是分类已废弃？）"
        )

    if not args.quiet:
        print(f"候选总数: {len(cand['candidates'])}")
        print(f"distinct vertical 值: {len(used)}")
        print(f"来源类别登记: {len(classes)} / 数据里出现 {len([v for v in used if v in single])}")
        print(f"主题登记: {len(topics)} / 数据里出现 {len([v for v in used if v not in single])}")

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    if not args.quiet:
        print("OK: 登记表与候选数据双向对齐（无未登记取值，无死条目）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

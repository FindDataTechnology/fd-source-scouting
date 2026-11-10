#!/usr/bin/env python3
"""golden 基线校验器：`replay/golden-side.json` 的结构与 kind 闭集。

**为什么需要**（2026-11-10）：全仓 grep 确认该文件**只有文档引用、没有代码消费者**——
既没有 `probed_404` 的穷举分支，也就**没有任何东西会拦住**它腐化。同一天刚发生的事实：
N5 的 kind 由 `probed_404` 改成 `probed_available`（CP112 实测可得），若有消费者按旧值
分支，会静默走旧路径。故把"kind 是闭集"这件事从口头约定变成闸门。

判据：
1. `schema` 必须是 `hotel-replay-golden/v1`
2. 每条负例 `kind` ∈ `KNOWN_KINDS`（新增 kind 必须同时改本文件——这是刻意的：
   新 kind 意味着有下游要学它，不该静默扩大）
3. 带 `superseded` 块的条目必须齐四要素（原结论/推翻日/证据/决定记录）——
   结论反转可以，但不能只改字不留痕
4. `positive_series` 的 id 唯一；每条必备字段齐全

用法：
    python3 data-source-scouting/scripts/validate_golden.py
    python3 data-source-scouting/scripts/validate_golden.py --path <other.json>

退出码：0=通过；1=有违规（逐条点名）；2=文件不可读。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # finddata 根
DEFAULT = ROOT / "openspec" / "changes" / "industry-source-solution-fleet" / "replay" / "golden-side.json"

SCHEMA = "hotel-replay-golden/v1"
KNOWN_KINDS = ("code_level_evidence", "probed_404", "probed_available", "caliber_trap")
SUPERSEDED_REQUIRED = ("原结论", "推翻日", "证据", "决定记录")
SERIES_REQUIRED = ("id", "concept", "granularity", "window", "periods", "trend_gate")


def validate(doc: dict) -> list[str]:
    bad: list[str] = []
    if doc.get("schema") != SCHEMA:
        bad.append(f"schema 应为 {SCHEMA}，实为 {doc.get('schema')!r}")

    for key in ("meta_conclusions", "positive_series", "negative_conclusions", "adjudication_rules"):
        if not isinstance(doc.get(key), list) or not doc.get(key):
            bad.append(f"{key} 缺失或为空")

    seen_series: set[str] = set()
    for s in doc.get("positive_series") or []:
        sid = s.get("id")
        if not sid:
            bad.append("positive_series 有条目缺 id")
            continue
        if sid in seen_series:
            bad.append(f"positive_series id 重复：{sid}")
        seen_series.add(sid)
        for f in SERIES_REQUIRED:
            if f not in s:
                bad.append(f"positive_series {sid} 缺字段 {f}")

    seen_neg: set[str] = set()
    for n in doc.get("negative_conclusions") or []:
        nid = n.get("id")
        if not nid:
            bad.append("negative_conclusions 有条目缺 id")
            continue
        if nid in seen_neg:
            bad.append(f"negative_conclusions id 重复：{nid}")
        seen_neg.add(nid)
        kind = n.get("kind")
        if kind not in KNOWN_KINDS:
            bad.append(
                f"负例 {nid} 的 kind={kind!r} 不在闭集 {KNOWN_KINDS}。"
                f"新增 kind 必须同时更新本校验器（避免下游按旧值静默分支）"
            )
        if "superseded" in n:
            sup = n["superseded"] or {}
            missing = [k for k in SUPERSEDED_REQUIRED if not sup.get(k)]
            if missing:
                bad.append(f"负例 {nid} 的 superseded 块缺 {missing}（结论反转必须留痕）")
        if not n.get("claim"):
            bad.append(f"负例 {nid} 缺 claim")
    return bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT))
    args = ap.parse_args(argv[1:])

    p = Path(args.path)
    if not p.exists():
        print(f"✗ 文件不存在：{p}", file=sys.stderr)
        return 2
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"✗ JSON 不可解析：{exc}", file=sys.stderr)
        return 2

    bad = validate(doc)
    negs = doc.get("negative_conclusions") or []
    kinds = sorted({n.get("kind") for n in negs if isinstance(n, dict)})
    print(f"golden 基线：负例 {len(negs)} 条，kind 分布 {kinds}")
    for b in bad:
        print(f"  ✗ {b}")
    print(f"checked，violations={len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

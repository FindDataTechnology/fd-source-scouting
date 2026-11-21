#!/usr/bin/env python3
"""把手写 overrides 合并进派生候选清单（change structure-scout-candidates）。

为什么要有这个文件
──────────────────
``candidates.json`` 是 ``extract_candidates.py`` 的**派生输出**——重抽即整体覆写。
任何写进去的人写字段活不过一次重跑。仓库里已经撞过这个坑：``ontology-alignment.json``
的存在理由就是「2026-11-19 实测：加在 candidates.json 里的对齐声明在重跑后消失」。

所以人的判断（落地归属、退役原因、解析分诊）存 ``candidates.overrides.json``，
本脚本在抽取后把它合并进派生输出。**派生输出不手改。**

合并语义
────────
* ``landed_as``        → 覆写 ``landed_slug``
* ``reconciliation``   → 写 ``reconciliation``（landed_as / never_landed / dropped）
* ``dropped_archive``  → 写 ``dropped_archive``
* ``review_reason``    → 写 ``review_reason``

幂等：同一份 overrides 跑两遍结果一致。找不到对应候选的 override 会被报出
（口径：overrides 引用了不存在的候选 = 抽取漏了它或键名写错，两种都要人看）。

用法::

    python3 scripts/apply_overrides.py            # 就地合并
    python3 scripts/apply_overrides.py --check    # 只报差，不写
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # finddata/
CANDIDATES = ROOT / "data-source-scouting" / "candidates.json"
OVERRIDES = ROOT / "data-source-scouting" / "candidates.overrides.json"

FIELDS = ("landed_as", "reconciliation", "dropped_archive", "review_reason")


def load() -> tuple[dict, dict]:
    cand = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    ov = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.is_file() else {}
    return cand, (ov.get("overrides") or {})


def apply_one(entry: dict, spec: dict) -> bool:
    """合并一条 override；返回是否改动。"""
    changed = False
    la = spec.get("landed_as")
    if la is not None and entry.get("landed_slug") != la:
        entry["landed_slug"] = la
        changed = True
    for f in ("reconciliation", "dropped_archive", "review_reason"):
        v = spec.get(f)
        if v is not None and entry.get(f) != v:
            entry[f] = v
            changed = True
    return changed


def apply(cand: dict, overrides: dict) -> tuple[int, list[str]]:
    by_id = {c.get("id") or c.get("name"): c for c in cand.get("candidates", [])}
    changed = 0
    orphan = []
    for key, spec in overrides.items():
        entry = by_id.get(key)
        if entry is None:
            orphan.append(key)
            continue
        if apply_one(entry, spec):
            changed += 1
    return changed, orphan


def main() -> int:
    ap = argparse.ArgumentParser(prog="apply_overrides")
    ap.add_argument("--check", action="store_true", help="只报差，不写")
    args = ap.parse_args()

    if not CANDIDATES.is_file():
        print(f"判不出：{CANDIDATES} 不存在", file=sys.stderr)
        return 2
    cand, overrides = load()
    changed, orphan = apply(cand, overrides)

    for k in orphan:
        print(f"  ! override 引用了不存在的候选：{k}", file=sys.stderr)
    print(f"合并 {len(overrides)} 条 override，改动 {changed} 条候选"
          + ("（--check，未写盘）" if args.check else ""))
    if not args.check and changed:
        CANDIDATES.write_text(json.dumps(cand, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    return 1 if orphan else 0


if __name__ == "__main__":
    sys.exit(main())

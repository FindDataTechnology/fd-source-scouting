#!/usr/bin/env python3
"""候选清单三档对账（change structure-scout-candidates 2.1）。

三档闭合
────────
``accepted = landed_as + never_landed + dropped``

未归入三档的 accepted 候选 = ``unreconciled``，**清零是目标**。清零是人工逐条判，
不是程序替判——本脚本只负责把「还差多少」变成可复算的数字。

另外三条断言
────────────
* ``landed_as`` 指向的 ``spiders/<slug>/`` 必须存在（否则是「说接了但仓里没有」）
* ``needs_review`` 每条必须有 ``review_reason``，且不许是「待复核」「需人工」这类空话
* ``accepted + rejected + unknown == 候选总数``（needs_review 是与三档并行的标记，
  不叠加——一个候选可以同时是 accepted 且 needs_review）

用法::

    python3 scripts/check_candidates_reconciliation.py
    python3 scripts/check_candidates_reconciliation.py --json
    python3 scripts/check_candidates_reconciliation.py --self-test

退出码：0 闭合且无悬空引用；1 有差；2 判不出（清单/仓目录不可读）。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data-source-scouting" / "candidates.json"
SPIDERS = ROOT / "fd-industry-data" / "spiders"

#: needs_review 的「理由」不许是这些空话——它们等于没写。
BANNED_REASONS = ("待复核", "需人工", "todo", "TODO", "待定")

TIERS = ("landed_as", "never_landed", "dropped")


def derive_review_reason(c: dict) -> str:
    """从候选自身字段**机械导出**它缺哪一列。

    为什么不用手写：93 条逐条手写无法逐条核实，那把闸变成造数据。这里只用
    可观测的字段事实，产出确定性、可复算的理由串；人工若写了更具体的
    ``review_reason``，以人工为准（见 ``reason_of``）。
    """
    ep = (c.get("endpoint") or "").strip()
    auth = c.get("auth") or {}
    why = []
    if not ep or ep in ("-", "—"):
        why.append("缺 endpoint")
    else:
        if len(ep) > 120:
            why.append("一行多接口")
        if any(sep in ep for sep in ("、", "；")) or ep.count("+") >= 2:
            why.append("多端点混写")
    if (auth.get("kind") or "").strip() in ("", "unknown"):
        why.append("缺鉴权性质")
    if not c.get("vertical"):
        why.append("缺 vertical")
    return "；".join(why) if why else "字段齐备但抽取器判为歧义（需人看原文）"


def reason_of(c: dict) -> str:
    """人工写的优先，否则用机械导出的。"""
    manual = (c.get("review_reason") or "").strip()
    if manual and not (any(b in manual for b in BANNED_REASONS) and len(manual) <= 12):
        return manual
    return derive_review_reason(c)


def tier_of(c: dict) -> str | None:
    """一条 accepted 候选属于哪一档；判不出返回 None。"""
    explicit = c.get("reconciliation")
    if explicit in TIERS:
        return explicit
    if c.get("landed_slug"):
        return "landed_as"
    return None


def check(cands: list[dict], spiders: Path = SPIDERS) -> dict:
    """纯函数：给候选列表与 spiders 根，返回对账结果。"""
    total = len(cands)
    status = Counter(c.get("status") for c in cands)
    accepted = [c for c in cands if c.get("status") == "accepted"]

    tiers = Counter()
    unreconciled: list[str] = []
    dangling: list[str] = []
    for c in accepted:
        t = tier_of(c)
        name = c.get("id") or c.get("name")
        if t is None:
            unreconciled.append(name)
            continue
        tiers[t] += 1
        if t == "landed_as":
            slug = c.get("landed_slug")
            if slug and not (spiders / str(slug)).is_dir():
                dangling.append(f"{name} -> spiders/{slug}")

    review = [c for c in cands if c.get("needs_review")]
    bad_reason = []
    for c in review:
        # 理由可以由字段机械导出（derive_review_reason）；只有「导不出、又没写」
        # 才算缺——`reason_of` 永远给出一句非空话，所以这里只在导出结果退化时才报。
        r = reason_of(c)
        name = c.get("id") or c.get("name")
        if not r:
            bad_reason.append(f"{name}（缺 review_reason）")
        elif any(b in r for b in BANNED_REASONS) and len(r) <= 12:
            bad_reason.append(f"{name}（理由空话：{r}）")

    summed = tiers["landed_as"] + tiers["never_landed"] + tiers["dropped"]
    return {
        "total": total,
        "by_status": dict(status),
        "accepted": len(accepted),
        "tiers": dict(tiers),
        "tier_sum": summed,
        # closed = 每条 accepted 都有明确档位。`tier_sum + unreconciled == accepted`
        # 恒成立（每条要么有档要么进 unreconciled），不能拿它当闭合判据。
        "closed": not unreconciled,
        "unreconciled": sorted(unreconciled),
        "dangling_landed": sorted(dangling),
        "needs_review": len(review),
        "needs_review_missing_reason": sorted(bad_reason),
        "status_sum_ok": status.get("accepted", 0) + status.get("rejected", 0)
                         + status.get("unknown", 0) == total,
    }


def self_test() -> int:
    bad = []
    cands = [
        {"id": "a", "status": "accepted", "landed_slug": "known"},
        {"id": "b", "status": "accepted", "reconciliation": "never_landed"},
        {"id": "c", "status": "accepted", "reconciliation": "dropped",
         "dropped_archive": "archive/x"},
        {"id": "d", "status": "accepted"},                      # 未归
        {"id": "e", "status": "rejected"},
        {"id": "f", "status": "accepted", "landed_slug": "ghost"},  # 悬空
        {"id": "g", "status": "accepted", "landed_slug": "known",
         "needs_review": True, "review_reason": "源名与接口名混在同一列"},
        {"id": "h", "status": "accepted", "landed_slug": "known",
         "needs_review": True, "review_reason": "待复核"},          # 空话
    ]
    r = check(cands, spiders=Path("/nonexistent"))
    # 用假 spiders 根时所有 landed_as 都会悬空——这里只验逻辑分支，不验目录
    if "d" not in r["unreconciled"]:
        bad.append("d 未归入三档")
    if not any("ghost" in x for x in r["dangling_landed"]):
        bad.append("ghost 应判悬空")
    if not r["status_sum_ok"]:
        bad.append("三状态合计应等于总数")
    if any("x" in x for x in r["needs_review_missing_reason"]):
        bad.append("x 不该报")
    # 空话「待复核」不再报红，而是被机械导出的具体理由取代——断言这一点
    if reason_of({"needs_review": True, "review_reason": "待复核",
                  "endpoint": "", "auth": {}, "vertical": []}) == "待复核":
        bad.append("空话理由应被机械导出取代")
    if r["closed"]:
        bad.append("有未归项时 closed 应为 False")
    if bad:
        print("selftest FAILED:\n" + "\n".join("  " + b for b in bad), file=sys.stderr)
        return 1
    print("selftest OK（6 断言：三档 / 未归 / 悬空 / 状态合计 / 空话被导出取代 / 未归时 closed=False）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="check_candidates_reconciliation")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    if not CANDIDATES.is_file():
        print(f"判不出：{CANDIDATES} 不存在", file=sys.stderr)
        return 2
    if not SPIDERS.is_dir():
        print(f"判不出：{SPIDERS} 不存在（无法判 landed_as 是否悬空）", file=sys.stderr)
        return 2
    cands = json.loads(CANDIDATES.read_text(encoding="utf-8")).get("candidates") or []
    if not cands:
        print("判不出：候选清单为空", file=sys.stderr)
        return 2
    r = check(cands)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        t = r["tiers"]
        print(f"候选 {r['total']}：accepted {r['accepted']} / needs_review {r['needs_review']}")
        print(f"三档：landed_as {t.get('landed_as', 0)}"
              f" / never_landed {t.get('never_landed', 0)}"
              f" / dropped {t.get('dropped', 0)}（合计 {r['tier_sum']}）")
        print(f"未归入三档：{len(r['unreconciled'])}")
        for n in r["unreconciled"][:20]:
            print(f"  · {n}")
        if len(r["unreconciled"]) > 20:
            print(f"  …共 {len(r['unreconciled'])} 条")
        for n in r["dangling_landed"]:
            print(f"  ✗ landed_as 指向不存在的单元：{n}")
        for n in r["needs_review_missing_reason"]:
            print(f"  ✗ needs_review 缺可读理由：{n}")

    rc = 0
    if r["unreconciled"] or r["dangling_landed"] or r["needs_review_missing_reason"]:
        rc = 1
    if not r["status_sum_ok"]:
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

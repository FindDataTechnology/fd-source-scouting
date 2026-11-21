"""候选清单三档对账（change structure-scout-candidates 2.1）。

**为什么要有这条测试**：75% 的候选（146 accepted 里 51 条）曾「侦察簿说接了、
仓里找不到落点」。三档（landed_as / never_landed / dropped）不闭合时，任何
「还有多少候选没落仓」的读数都不可信。

最容易坏的方式是 `closed` 的判据写错：`tier_sum + unreconciled == accepted`
是恒等式（每条要么有档要么进 unreconciled），拿它当闭合判据会永远绿。
真正该问的是「还有没有未归项」。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCOUTING = HERE.parent                              # data-source-scouting
FINDDATA = SCOUTING.parent                          # finddata/
sys.path.insert(0, str(SCOUTING / "scripts"))

import check_candidates_reconciliation as ccr  # noqa: E402


CANDS = [
    {"id": "a", "status": "accepted", "landed_slug": "known"},
    {"id": "b", "status": "accepted", "reconciliation": "never_landed"},
    {"id": "c", "status": "accepted", "reconciliation": "dropped",
     "dropped_archive": "archive/x"},
    {"id": "d", "status": "accepted"},                        # 未归
    {"id": "e", "status": "rejected"},
    {"id": "f", "status": "accepted", "landed_slug": "ghost"},  # 悬空
    {"id": "g", "status": "accepted", "landed_slug": "known",
     "needs_review": True, "review_reason": "源名与接口名混在同一列"},
    {"id": "h", "status": "accepted", "landed_slug": "known",
     "needs_review": True, "review_reason": "待复核"},          # 空话
    {"id": "i", "status": "unknown", "needs_review": True,
     "endpoint": "", "auth": {}, "vertical": []},              # 字段全缺
]


def _check(spiders: Path):
    return ccr.check(CANDS, spiders=spiders)


def test_tiers_are_mutually_exclusive():
    r = _check(Path("/nonexistent"))
    t = r["tiers"]
    assert t["landed_as"] == 4, t       # a, f（悬空但仍算 landed_as）, g, h
    assert t["never_landed"] == 1 and t["dropped"] == 1
    assert r["tier_sum"] == t["landed_as"] + t["never_landed"] + t["dropped"]


def test_unreconciled_is_listed():
    r = _check(Path("/nonexistent"))
    assert "d" in r["unreconciled"]


def test_dangling_landed_slug_is_flagged():
    """landed_slug 指向不存在的单元 = 「说接了但仓里没有」。"""
    r = _check(Path("/nonexistent"))
    assert any("ghost" in x for x in r["dangling_landed"])


def test_status_sum_must_equal_total():
    r = _check(Path("/nonexistent"))
    assert r["status_sum_ok"]
    broken = CANDS + [{"id": "j", "status": "bogus"}]
    assert not ccr.check(broken, spiders=Path("/x"))["status_sum_ok"]


def test_closed_is_not_an_identity():
    """有未归项时 closed 必须 False —— 它不能是恒等式。"""
    r = _check(Path("/nonexistent"))
    assert r["unreconciled"] and r["closed"] is False


def test_banned_reason_is_replaced_not_accepted():
    """空话「待复核」由机械导出的具体理由取代，不许原样当成合格理由。"""
    empty = {"needs_review": True, "review_reason": "待复核",
             "endpoint": "", "auth": {}, "vertical": []}
    got = ccr.reason_of(empty)
    assert got != "待复核"
    assert "缺 endpoint" in got and "缺鉴权性质" in got


def test_manual_reason_wins():
    c = {"needs_review": True, "review_reason": "源名与接口名混在同一列"}
    assert ccr.reason_of(c) == "源名与接口名混在同一列"


def test_real_candidates_are_closed():
    """真盘面：三档必须闭合（这是本 change 的交付判据）。"""
    import json

    p = SCOUTING / "candidates.json"
    if not p.is_file():
        import pytest
        pytest.skip("无候选清单")
    cands = json.loads(p.read_text(encoding="utf-8")).get("candidates") or []
    spiders = FINDDATA / "fd-industry-data" / "spiders"
    if not spiders.is_dir():
        import pytest
        pytest.skip("无 spiders/")
    r = ccr.check(cands, spiders=spiders)
    assert r["closed"], f"未归入三档：{r['unreconciled']}"
    assert r["tier_sum"] == r["accepted"], (r["tier_sum"], r["accepted"])
    assert not r["dangling_landed"], r["dangling_landed"]

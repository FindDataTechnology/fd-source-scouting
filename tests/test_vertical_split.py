"""The vertical column was overloaded; this splits it without rewriting it.

`candidates.json` stored two orthogonal dimensions in one `vertical` array: the
main document's section letters (A–N = source *class*) and topic words
(半导体/货币市场/…). Any statistic grouped by that column was answering two
different questions at once, so it answered neither.

Two invariants this file pins, both learnt the hard way:

- **the original column is never rewritten** — it carries the classification
  intent of whoever wrote it, and a bad normalisation must stay reversible;
- **an unregistered value is refused**, not invented on the spot — a value
  nobody registered is a decision nobody made.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

import extract_candidates as ex  # noqa: E402
import check_vertical_registry as chk  # noqa: E402


# ------------------------------------------------------------------ splitting


def test_single_letters_are_source_class_not_topic():
    classes, topics = ex.split_verticals(["K", "商务部数据中心"])
    assert classes == ["K"]
    assert topics == []


def test_topic_words_go_to_topic():
    classes, topics = ex.split_verticals(["半导体", "医药"])
    assert classes == []
    assert topics == ["半导体", "医药"]


def test_mixed_row_splits_into_both():
    classes, topics = ex.split_verticals(["B", "灾害"])
    assert classes == ["B"]
    assert topics == ["灾害"]


def test_unregistered_value_is_neither():
    """It must fall through both lists so the caller can refuse it."""
    classes, topics = ex.split_verticals(["新发明的分类"])
    assert classes == [] and topics == []


# ------------------------------------------------------------------- registry


def test_registry_covers_every_value_in_the_data():
    cand = json.loads((ROOT / "candidates.json").read_text(encoding="utf-8"))
    reg = json.loads((ROOT / "vertical-registry.json").read_text(encoding="utf-8"))
    classes = set(reg["dimensions"]["source_class"]["values"])
    topics = set(reg["dimensions"]["topic"]["values"])
    single = set(reg["mapping"]["single_letter_to_source_class"])
    if not cand["candidates"]:
        pytest.skip("no candidates extracted")

    homeless = set()
    for row in cand["candidates"]:
        for v in row.get("vertical") or []:
            pool = classes if v in single else topics
            if v not in pool:
                homeless.add(v)
    assert not homeless, f"unregistered vertical value(s): {sorted(homeless)}"


def test_the_checker_can_fail(tmp_path, monkeypatch):
    """A gate that has never been red is not a gate.

    Drop a registered value from a copy of the registry and assert the checker
    reports it by name — otherwise this whole file would pass on a registry that
    checks nothing.
    """
    reg = json.loads((ROOT / "vertical-registry.json").read_text(encoding="utf-8"))
    victim = "半导体"
    assert victim in reg["dimensions"]["topic"]["values"], "pick a real value"
    del reg["dimensions"]["topic"]["values"][victim]

    broken = tmp_path / "vertical-registry.json"
    broken.write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(chk, "REGISTRY", broken)

    rc = chk.main(["--quiet"])
    assert rc == 1, "the checker must fail when a used value has no home"


# ------------------------------------------------------- non-destructive rule


def test_original_vertical_is_untouched_by_extraction():
    """Re-running the extractor must not rewrite the historical column."""
    before = json.loads((ROOT / "candidates.json").read_text(encoding="utf-8"))
    orig = [r.get("vertical") for r in before["candidates"]]
    if not orig:
        pytest.skip("no candidates")

    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "extract_candidates.py")],
        capture_output=True, text=True, cwd=ROOT, timeout=300,
    )
    assert out.returncode == 0, out.stderr[-2000:]

    after = json.loads((ROOT / "candidates.json").read_text(encoding="utf-8"))
    now = [r.get("vertical") for r in after["candidates"]]
    assert now == orig, "the extractor rewrote the original vertical column"


# --------------------------------------------------- task 1.3: mapping table


def test_topic_values_carry_a_kind():
    """39 topics split into four kinds; an unkinded topic answers nothing.

    The kinds matter because 'industry', 'market' and 'financial_face' are not
    the same axis — grouping a bank's regulatory report face with a commodity
    price source under one 'industry' label would be a category error.
    """
    reg = json.loads((ROOT / "vertical-registry.json").read_text(encoding="utf-8"))
    topics = reg["dimensions"]["topic"]["values"]
    missing = [k for k, v in topics.items() if "kind" not in v]
    assert not missing, f"topics without a kind: {missing}"
    kinds = {v["kind"] for v in topics.values()}
    assert kinds == {"industry", "market", "financial_face", "meta"}


def test_mapping_table_covers_every_value(capsys):
    """Task 1.3: the dry-run tie-out prints all 53 values with a destination."""
    rc = chk.main(["--quiet", "--mapping-table"])
    out = capsys.readouterr().out
    rows = [ln for ln in out.splitlines() if "恒等" in ln or "归一到" in ln]
    assert len(rows) == 53, f"expected 53 rows, got {len(rows)}"
    assert rc == 0


def test_deliberate_non_merges_are_recorded():
    """Not merging is a decision, and an undocumented one gets re-litigated."""
    reg = json.loads((ROOT / "vertical-registry.json").read_text(encoding="utf-8"))
    rejected = reg["normalization"]["_rejected_merges"]
    assert len(rejected) == 5
    for pair, why in rejected.items():
        assert why and len(why) > 10, f"{pair} has no real reason"


def test_single_letters_are_identity_mapped():
    """A–N ARE the canonical values (they are the document's section numbers).

    Verified against the document: A's users are Eurostat/UN Comtrade (international
    official statistics), K's are 商务部/工信部 (Chinese ministries). No renaming
    needed — renaming would break the tie to the source document.
    """
    reg = json.loads((ROOT / "vertical-registry.json").read_text(encoding="utf-8"))
    aliases = reg["normalization"].get("aliases") or {}
    for letter in reg["mapping"]["single_letter_to_source_class"]:
        assert letter not in aliases, f"{letter} should not be an alias of anything"

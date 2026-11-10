#!/usr/bin/env python3
"""已知陷阱回归探测：把「已经定过性的结论」变成可执行的漂移检测。

**为什么需要它**：酒店线回放（`replay/adjudication.md` 4.3）暴露了一个机制缺口——
执行侧把探针预算全给了新候选，对 golden 已知的负例（census 无住宿类目、jp-estat 需
appid、Eurostat 无住宿价格指数）一条都没复测。根因不是懒，是**没有清单可依**。
本脚本就是那份清单：读 `regression-traps.json`，逐条探测，只回答一件事——

    这条结论现在是否仍然成立？

变了 ≠ 可以接。变了意味着**解锁条件变化**，下一步是重侦察（见每条 `if_changed`），
不是直接出生成单。所以本脚本的产物是「漂移清单」，不是「接入决定」。

用法：
    python3 data-source-scouting/scripts/regression_probe.py            # 全量探测并落证据
    python3 data-source-scouting/scripts/regression_probe.py --check     # 只打印，不写文件
    python3 data-source-scouting/scripts/regression_probe.py --only nbs-easyquery-blocked

退出码：0=全部与预期一致；1=有漂移；2=探测本身失败（探针缺失/清单坏）。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # finddata 根
TRAPS = ROOT / "data-source-scouting" / "regression-traps.json"
EVIDENCE = ROOT / "data-source-scouting" / "evidence"
PROBE_BIN = ROOT / "fd-source-probe" / ".venv" / "bin" / "fd-source-probe"


def probe_one(binary: Path, trap: dict) -> dict:
    """跑一次探针，返回 (kind, status, evidence_path)。探针不可用时抛错。"""
    spec = trap.get("probe") or {}
    url = spec.get("url")
    if not url:
        return {"error": "trap 缺 probe.url"}
    out = EVIDENCE / "tmp" / f"regression-{trap['id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(binary), "probe", url, "--label", f"regression/{trap['id']}",
           "--caller", "scouting/regression_probe", "--json-out", str(out)]
    # 陷阱断言的是**结构**（表格/JSON 字段），标记常在 2KB 之后。
    # 实测教训（2026-11-10 第四批）：同一条 URL，默认 2048B 判 caliber_mismatch、
    # 65536B 判 ok——不是源变了，是 expect_contains 只对截断前缀匹配。
    # 故回归探测单独放宽窗口，可按 trap 覆盖。
    env = dict(os.environ)
    env["FD_PROBE_MAX_BODY_BYTES"] = str(
        int((spec.get("max_body_bytes") or 65536)))
    # method/body 必须一起传：只传 header 会把陷阱里的 POST 全打成 GET
    # ——第四批实测症状：zhejiang 拿不到 sourceCode、data-europa 返 406。
    if spec.get("method"):
        cmd += ["--method", str(spec["method"])]
    for k, v in (spec.get("headers") or {}).items():
        cmd += ["--header", f"{k}:{v}"]
    if spec.get("body") is not None:
        cmd += ["--body", str(spec["body"])]
    if spec.get("expect_contains"):
        cmd += ["--expect-contains", spec["expect_contains"]]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
    try:
        doc = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "error": "探针无输出",
            "stderr": (proc.stderr or "")[-200:],
        }
    out.unlink(missing_ok=True)
    return {
        "kind": doc["verdict"]["kind"],
        "status": doc["status"],
        "reason": doc["verdict"]["reason"],
        "exit": (doc.get("exit") or {}).get("identity"),
        "body_prefix": doc.get("body_prefix", "")[:200],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="只打印，不写证据文件")
    ap.add_argument("--only", action="append", default=[], help="只跑指定 trap id（可重复）")
    ap.add_argument("--binary", default=str(PROBE_BIN), help="探针可执行文件路径")
    args = ap.parse_args(argv[1:])

    binary = Path(args.binary)
    if not binary.exists():
        print(f"探针不存在：{binary}（先 `cd fd-source-probe && uv pip install -e .`）",
              file=sys.stderr)
        return 2
    try:
        traps = json.loads(TRAPS.read_text(encoding="utf-8"))["traps"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"陷阱清单不可读：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    selected = [t for t in traps if not args.only or t["id"] in args.only]
    rows, drifted = [], []
    for trap in selected:
        got = probe_one(binary, trap)
        expect = (trap.get("expect") or {}).get("kind")
        if "error" in got:
            verdict = "probe_error"
        elif trap.get("disputed"):
            # 不可复现/两侧证据冲突的旧结论：不判漂移也不判一致，交人工裁决。
            verdict = "disputed"
        elif got["kind"] == expect:
            verdict = "unchanged"
        else:
            verdict = "drifted"
            drifted.append(trap["id"])
        rows.append({"trap": trap, "got": got, "expect": expect, "verdict": verdict})
        flag = {"unchanged": "=", "drifted": "≠", "probe_error": "!",
                "disputed": "?"}[verdict]
        print(f"  {flag} {trap['id']:34} expect={str(expect):18} "
              f"got={str(got.get('kind')):18} status={got.get('status')}")

    print(f"\n合计 {len(rows)}：一致 {sum(1 for r in rows if r['verdict']=='unchanged')}"
          f" / 漂移 {len(drifted)} / 待裁决 {sum(1 for r in rows if r['verdict']=='disputed')}"
          f" / 探测失败 {sum(1 for r in rows if r['verdict']=='probe_error')}")
    if drifted:
        print("\n漂移项（变了 ≠ 可以接：下一步是重侦察，不是出单）：")
        for rid in drifted:
            trap = next(t for t in selected if t["id"] == rid)
            print(f"  - {rid}：{trap.get('if_changed', '（未写解锁动作）')}")

    if args.check:
        return 0 if not drifted else 1
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    path = EVIDENCE / f"regression-{stamp}.json"
    path.write_text(
        json.dumps(
            {
                "schema": "source-regression-run/v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "traps_file": "data-source-scouting/regression-traps.json",
                "rows": rows,
                "drifted": drifted,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"\n-> {path}")
    return 0 if not drifted else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

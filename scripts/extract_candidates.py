#!/usr/bin/env python3
"""把侦察簿的候选表转成结构化清单 `data-source-scouting/candidates.json`。

**为什么不硬解析整份文档**：`docs/onboarding-funnel.md` 已经写明——侦察簿是 1253 行、
十几套异构表头的手写文档，硬解析得到的是"没人能复算"的数。本脚本因此只做两件确定的事：

1. **按表头签名白名单抽取**：只转换签名被显式登记过的表（字段映射写在 `TABLE_SPECS`），
   每行落 `doc_line` 行号，供人工逐条对位。
2. **其余表全部计数上报**（`coverage.excluded_tables`，含表头、行数、行号），
   不静默丢表。丢一张表就等于让漏斗少算一批候选。

状态判定只用文档里已经写下的实测列（`直连` / `判定` / 成本-价值），不引入新判断：

- 直连列以 ✅ 开头 → accepted；以 ❌ 开头 → rejected（reason 取反爬/形态列）；
  混合/其它 → unknown。
- 无直连列但 ★接 段（章节标题含 ★接/星接）→ accepted；备选段 → candidate_unprobed；
  否决段（死胡同/维持放弃/降级）→ rejected。
- 其余 → unknown。

`landed_slug` 只在文档正文点名了既有单元时填（如"零新建（`un-comtrade`）"），
并与 `spiders/` 实际存在的目录比对；对不上就留 null，不猜。

用法：
    python3 data-source-scouting/scripts/extract_candidates.py            # 写 candidates.json
    python3 data-source-scouting/scripts/extract_candidates.py --check    # 只报表清单，不写文件
    python3 data-source-scouting/scripts/extract_candidates.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # finddata 根
DOC = ROOT / "data-source-scouting" / "INDUSTRY-DATA-SOURCES.md"
OUT = ROOT / "data-source-scouting" / "candidates.json"
SCHEMA_PATH = ROOT / "data-source-scouting" / "candidates.schema.json"
SPIDERS = ROOT / "fd-industry-data" / "spiders"
REGISTRY_PATH = ROOT / "data-source-scouting" / "vertical-registry.json"


def _load_registry() -> tuple[set[str], set[str]]:
    """(source classes, topics) from vertical-registry.json.

    Read at import so the extractor refuses an unregistered value instead of
    inventing a classification on the spot — a value nobody registered is a
    decision nobody made, and letting it through silently fragments the history.
    """
    body = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    dims = body["dimensions"]
    return (
        set(dims["source_class"]["values"]),
        set(dims["topic"]["values"]),
    )


_REGISTRY_SINGLE, _REGISTRY_TOPICS = _load_registry()


def split_verticals(values: list[str]) -> tuple[list[str], list[str]]:
    """Partition the overloaded column into its two orthogonal dimensions.

    A–N are the main document's section numbers (source *class*); everything else
    is a *topic*. Keeping them apart is the whole point: grouping by the original
    column answers two different questions at once and therefore neither.
    """
    classes, topics = [], []
    for v in values:
        if v in _REGISTRY_SINGLE:
            classes.append(v)
        elif v in _REGISTRY_TOPICS:
            topics.append(v)
    return classes, topics

SCHEMA = "source-candidates/v1"
GENERATOR = "extract_candidates.py/1.0"


@dataclass
class TableSpec:
    """一张被登记的表：表头签名 → 字段映射。

    ``signature`` 是表头单元格（去空白后）的元组；只有完全命中才抽取——
    近似命中一律视为未登记，进 excluded 表清单。
    """

    signature: tuple[str, ...]
    # 表头单元格名 → 目标字段
    mapping: dict[str, str]
    status_rule: str          # section_accept | section_candidate | section_reject | reach | verdict
    note: str = ""


# ---------------------------------------------------------------------------
# 已登记的表（新增表必须先在这里加签名，否则只会进 excluded 清单）
# ---------------------------------------------------------------------------
TABLE_SPECS: list[TableSpec] = [
    TableSpec(
        signature=("#", "源", "方向", "端点要点", "鉴权", "周期", "直连/代理"),
        mapping={
            "源": "name", "方向": "vertical", "端点要点": "endpoint",
            "鉴权": "auth", "周期": "cadence", "直连/代理": "reach",
        },
        status_rule="section_accept",
        note="Wave1 ★接 候选总表",
    ),
    TableSpec(
        signature=("源", "垂直", "要点"),
        mapping={"源": "name", "垂直": "vertical", "要点": "endpoint"},
        status_rule="section_accept",
        note="Wave2 新增 ★接 / 部分放宽段",
    ),
    TableSpec(
        signature=("源", "方向", "要点"),
        mapping={"源": "name", "方向": "vertical", "要点": "endpoint"},
        status_rule="section_accept",
        note="Wave3 新增 ★接",
    ),
    TableSpec(
        signature=("#", "源", "方向", "端点要点", "鉴权", "周期", "成本"),
        mapping={
            "源": "name", "方向": "vertical", "端点要点": "endpoint",
            "鉴权": "auth", "周期": "cadence", "成本": "cost",
        },
        status_rule="section_accept",
        note="银行业专场 星接候选总表",
    ),
    TableSpec(
        signature=(
            "源", "端点(实测)", "直连", "形态", "鉴权", "周期", "历史深度",
            "反爬", "样本证据", "成本", "价值",
        ),
        mapping={
            "源": "name", "端点(实测)": "endpoint", "直连": "reach",
            "鉴权": "auth", "周期": "cadence", "历史深度": "history_depth",
            "反爬": "anti_bot", "样本证据": "evidence", "成本": "cost", "价值": "value",
        },
        status_rule="reach",
        note="花卉专场·中国境内（含反爬列）",
    ),
    TableSpec(
        signature=(
            "源", "端点(实测)", "直连", "形态", "鉴权", "周期", "历史深度",
            "样本证据", "成本", "价值",
        ),
        mapping={
            "源": "name", "端点(实测)": "endpoint", "直连": "reach",
            "鉴权": "auth", "周期": "cadence", "历史深度": "history_depth",
            "样本证据": "evidence", "成本": "cost", "价值": "value",
        },
        status_rule="reach",
        note="花卉专场·全球（无反爬列）",
    ),
    TableSpec(
        signature=("源", "判定", "关键事实"),
        mapping={"源": "name", "判定": "verdict", "关键事实": "evidence"},
        status_rule="verdict",
        note="判定型表（含接/不接/待定混合）",
    ),
    TableSpec(
        signature=("源", "主机", "形态", "周期", "最新", "判定"),
        mapping={
            "源": "name", "主机": "endpoint", "周期": "cadence",
            "最新": "evidence", "判定": "verdict",
        },
        status_rule="verdict",
        note="酒店/垂直 W0 复测表",
    ),
    TableSpec(
        signature=("源", "HTTP", "结构化产物", "判定"),
        mapping={"源": "name", "HTTP": "reach", "结构化产物": "endpoint", "判定": "verdict"},
        status_rule="verdict",
        note="HTTP 判定型表",
    ),
    TableSpec(
        signature=("候选", "市场", "实测结论", "依据"),
        mapping={"候选": "name", "市场": "vertical", "实测结论": "verdict", "依据": "evidence"},
        status_rule="verdict",
        note="候选市场型表",
    ),
    TableSpec(
        signature=("站点", "本轮实测", "降级结论"),
        mapping={"站点": "name", "本轮实测": "evidence", "降级结论": "verdict"},
        status_rule="verdict",
        note="P4 探针降级表（2026-11-10，无证据不出单首次生效）",
    ),
    TableSpec(
        signature=("源", "本轮实测（阳性标记 / 体内答复）", "定案"),
        mapping={"源": "name", "本轮实测（阳性标记 / 体内答复）": "evidence", "定案": "verdict"},
        status_rule="verdict",
        note="欠账复测队列第五批（凭据类）",
    ),
    TableSpec(
        signature=("源", "本轮实测（含阳性标记）", "定案"),
        mapping={"源": "name", "本轮实测（含阳性标记）": "evidence", "定案": "verdict"},
        status_rule="verdict",
        note="欠账复测队列第四批（带阳性断言）",
    ),
    TableSpec(
        signature=("源", "本轮实测", "定案"),
        mapping={"源": "name", "本轮实测": "evidence", "定案": "verdict"},
        status_rule="verdict",
        note="欠账复测队列第一批（2026-11-10，US 官方 5 条活性复测）",
    ),
]

SPECS_BY_SIGNATURE = {s.signature: s for s in TABLE_SPECS}


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SEP_RE = re.compile(r"^\|[\s:|-]+\|$")


ESC_PIPE = "\u0000PIPE\u0000"


def split_row(line: str) -> list[str]:
    """切表格行。**必须处理 `\\|` 转义**：侦察簿里有单元格内含转义竖线
    （如 shibor 行的 `memCode=\"…\"`），按裸 `|` 切会把后续列整体错位一格，
    实测导致 auth 里出现"拼接串）"这种垃圾值。"""
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    inner = inner.replace("\\|", ESC_PIPE)
    return [c.replace(ESC_PIPE, "|").strip() for c in inner.split("|")]


def clean_cell(text: str) -> str:
    """去 markdown 强调与反引号，保留原文（不补全、不改写）。"""
    t = text.replace("**", "").replace("`", "")
    return t.strip()


def slugify(name: str) -> str:
    t = clean_cell(name).lower()
    t = re.sub(r"[\s_/·（）()\[\]:：,，.。]+", "-", t)
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff-]", "", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "unnamed"


def auth_kind(raw: str) -> tuple[str, str]:
    t = clean_cell(raw)
    low = t.lower()
    if not t or t in {"—", "-"}:
        return "unknown", ""
    if "免费" in t and "key" in low:
        return "free_key", t
    if "key" in low or "appid" in low or "token" in low:
        return "free_key" if "免费" in t or "免费key" in t else "unknown", t
    if "付费" in t or "订阅" in t or "paid" in low:
        return "paid", t
    if "无" in t:
        return "none", t
    return "unknown", t


def reach_state(raw: str) -> tuple[str, str]:
    t = clean_cell(raw)
    if not t or t in {"—", "-"}:
        return "unknown", ""
    if t.startswith("✅"):
        return "direct_ok", t
    if t.startswith("❌"):
        return "blocked", t
    if t.startswith("混合"):
        return "mixed", t
    if "代理" in t:
        return "proxy_only", t
    return "unknown", t


VERDICT_ACCEPT = ("接", "纳入", "✅")
VERDICT_REJECT = ("放弃", "不接", "死", "不可得", "❌")


def verdict_state(raw: str) -> tuple[str, str]:
    t = clean_cell(raw)
    if not t:
        return "unknown", "文档未给判定"
    if any(m in t for m in VERDICT_REJECT):
        return "rejected", t
    if any(m in t for m in VERDICT_ACCEPT):
        return "accepted", ""
    return "unknown", t


@dataclass
class Table:
    header: tuple[str, ...]
    line: int
    section: str
    top: str = ""
    rows: list[tuple[int, list[str]]] = field(default_factory=list)


def parse_tables(lines: list[str]) -> tuple[list[Table], str]:
    """返回 (表清单, 最近标题)。表 = 表头 + 分隔行 + 连续数据行。"""
    tables: list[Table] = []
    section = ""
    top = ""
    i = 0
    while i < len(lines):
        m = HEADING_RE.match(lines[i])
        if m:
            section = m.group(2).strip()
            if len(m.group(1)) == 1:
                top = section
            i += 1
            continue
        is_header = (
            lines[i].lstrip().startswith("|")
            and i + 1 < len(lines)
            and SEP_RE.match(lines[i + 1].strip())
        )
        if is_header:
            header = tuple(clean_cell(c) for c in split_row(lines[i]))
            table = Table(header=header, line=i + 1, section=section, top=top)
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = split_row(lines[j])
                if not SEP_RE.match(lines[j].strip()):
                    table.rows.append((j + 1, cells))
                j += 1
            tables.append(table)
            i = j
            continue
        i += 1
    return tables, section


def landed_slugs() -> dict[str, str]:
    """已落仓单元的目录名集合（用于把文档点名的单元对到实际目录）。"""
    if not SPIDERS.exists():
        return {}
    return {p.name: p.name for p in SPIDERS.iterdir() if p.is_dir()}


def _bare(host: str) -> str:
    """www 归一：文档写裸域（miit.gov.cn），manifest 写全称（www.miit.gov.cn）——
    两侧都剥掉前导 www. 后再比。归属冲突仍由多 slug 丢弃兜底。"""
    h = host.lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def _hosts_of_unit(unit_dir: Path) -> set[str]:
    """单元声明的上游主机：manifest.yaml + spider.py 都扫（实测发现 sdmx.oecd.org /
    data-api.ecb.europa.eu 只出现在 spider.py，只扫 manifest 会漏对位）。"""
    import re as _re

    hosts: set[str] = set()
    for name in ("manifest.yaml", "spider.py"):
        f = unit_dir / name
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _re.finditer(r"https?://([a-zA-Z0-9.-]+)", text):
            hosts.add(m.group(1).lower().rstrip("."))
        if name == "manifest.yaml":
            for m in _re.finditer(r"^(?:site|host|base_url|upstream)\s*:\s*[\'\"?]*([a-zA-Z0-9.-]+\.[a-z]{2,})", text, _re.M):
                hosts.add(m.group(1).lower())
    return {h for h in hosts if "." in h and not h.endswith(".example")}


def landed_hosts() -> dict[str, str]:
    """裸域主机 → slug 索引。同名主机归属多单元时丢弃（歧义不猜）。"""
    if not SPIDERS.exists():
        return {}
    idx: dict[str, list[str]] = {}
    for unit in SPIDERS.iterdir():
        if not unit.is_dir():
            continue
        for h in _hosts_of_unit(unit):
            idx.setdefault(_bare(h), []).append(unit.name)
    out: dict[str, str] = {}
    for h, slugs in idx.items():
        if len(slugs) == 1:
            out[h] = slugs[0]
    return out


def match_by_host(row_text: str, hosts: dict[str, str]) -> str | None:
    """端点主机对位：行文本里出现的主机 == 某 manifest 声明的上游主机。

    这是**证据级**对位（两边都是机器可核的主机相等），置信高于名称归一；
    中文源名 ↔ 英文 slug 的断层就靠它补（Wave1 26 条"无落地出处"多数是这种）。
    多主机命中且归属不同单元 → 丢弃（歧义不猜）。
    """
    found: set[str] = set()
    # 抓**完整**主机 token（首版正则只锚了一个标签 + TLD，会把 data.mofcom.gov.cn
    # 截成 mofcom.gov.cn——self-test 当场抓出来）。边界：前导不能还是主机字符。
    for m in re.finditer(r"(?<![a-z0-9.-])([a-z0-9][a-z0-9.-]*\.[a-z]{2,})(?![a-z0-9-])", row_text.lower()):
        slug = hosts.get(_bare(m.group(1)))
        if slug:
            found.add(slug)
    if len(found) == 1:
        return next(iter(found))
    return None


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def landed_labels() -> dict[str, str]:
    """manifest label 字段 → slug（中文显示名 ↔ 英文目录名的又一条证据链）。"""
    if not SPIDERS.exists():
        return {}
    out: dict[str, str] = {}
    for mf in SPIDERS.glob("*/manifest.yaml"):
        try:
            m = re.search(r"^label:\s*(.+)$", mf.read_text(errors="replace"), re.M)
        except OSError:
            continue
        if m:
            out.setdefault(_norm_label(m.group(1)), mf.parent.name)
    return out


def _norm_label(text: str) -> str:
    return re.sub(r"[\s（）()·/\-—]+", "", text.lower())


def _label_tokens(text: str) -> set[str]:
    """归一后按 2 字符滑窗切块——中英混排、省略词、换序都能对上大半。"""
    key = _norm_label(text)
    return {key[i:i+2] for i in range(len(key) - 1)} if len(key) >= 2 else set()


def match_by_slug_token(row_text: str, slugs: dict[str, str]) -> str | None:
    """slug 词元对位：行文本含 slug 的显著词段（shibor / shclearing / disclosure-plan）。

    「Shibor」行写的是路径 /ags/ms/cm-u-bk-shibor/ShiborHis，主机对位没接上是因为
    manifest 声明的是 chinamoney.com.cn（多单元共享主机，歧义被丢弃）——但 slug 词段
    就在路径里。判据：slug 切词后，行文本含 ≥2 个词元或 1 个 ≥6 字符词元；多命中丢弃。
    """
    low = row_text.lower()
    found: set[str] = set()
    for slug in slugs:
        parts = [p for p in slug.split("-") if len(p) >= 4]
        strong = [p for p in parts if len(p) >= 6 and p in low]
        weak = [p for p in parts if p in low]
        if strong or len(weak) >= 2:
            found.add(slug)
    return next(iter(found)) if len(found) == 1 else None


def match_by_label(name: str, row_text: str, labels: dict[str, str]) -> str | None:
    """label 对位：**候选 name 的 2-gram 被 manifest label 覆盖** ≥0.6 且 ≥4 块。

    方向是刻意的：name 是短锚（「东财披露日历」8 块），label 是长句——拿长句覆盖率
    当分母会把真配上的判死（星级季报 0.25），拿短锚覆盖率才稳（东财披露日历 0.80、
    Shibor 1.00）。多命中=歧义丢弃；host 歧义（zwgk.mct.gov.cn 双单元）靠本链拆开。
    """
    nt = _label_tokens(name)  # 短锚=name，不是整行（整行当分母会让 Shibor 判不过）
    if len(nt) < 4:
        return None
    hits: set[str] = set()
    for lab, slug in labels.items():
        lt = _label_tokens(lab)
        if len(lt) < 2:
            continue
        covered = len(nt & lt) / len(nt)
        if covered >= 0.6 and len(nt & lt) >= 4:
            hits.add(slug)
    return next(iter(hits)) if len(hits) == 1 else None


def match_by_name(name: str, slugs: dict[str, str]) -> str | None:
    """名称归一对位：文档源名与单元目录名归一后相同，或单元名以源名为前缀。

    反引号对位是硬证据；这条是**低置信**对位（"UN Comtrade" ↔ `un-comtrade`），
    命中后仍标 needs_review，供人工一眼扫过。前缀匹配要求源名归一后 ≥5 字符，
    否则 `data` 这类短词会把一堆单元误配进来（实测踩过）。
    """
    key = _norm(name)
    if not key:
        return None
    exact = [s for s in slugs if _norm(s) == key]
    if len(exact) == 1:
        return exact[0]
    if len(key) >= 5:
        pref = [s for s in slugs if s.startswith(key + "-")]
        if len(pref) == 1:
            return pref[0]
    return None


def find_landed(text: str, slugs: dict[str, str]) -> tuple[str | None, bool]:
    """在行文本里找被**反引号点名**的既有单元。返回 (slug|None, 是否多义)。

    只认反引号是刻意的：侦察簿里单元名一律写作 `` `un-comtrade` ``。放开到裸文本
    会让 `data.mofcom.gov.cn` 命中名为 `data` 的目录（实测踩过：商务部那行被对到
    `spiders/data`），把"端点主机名"当成"已落仓证据"。
    """
    ticked = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", text))
    hits = sorted(t for t in ticked if t in slugs)
    if len(hits) == 1:
        return hits[0], False
    if len(hits) > 1:
        return None, True
    return None, False


def wave_of(section: str, top: str = "") -> str:
    """批次标签优先取一级标题（`# Wave 1 结果汇总` 才是批次）。"""
    for text in (top, section):
        for token in ("Wave 1", "Wave 2", "Wave 3", "银行业专场", "花卉专场",
                      "酒店行业专场", "餐饮行业专场", "普惠金融"):
            if token in text:
                return token
    return ""


def section_status_rule(section: str) -> str:
    if any(k in section for k in ("★接", "星接")):
        return "accept"
    if any(k in section for k in ("备选", "待复核")):
        return "candidate"
    if any(k in section for k in ("死胡同", "维持放弃", "降级", "放弃")):
        return "reject"
    return ""


def build(doc: Path = DOC) -> dict:
    raw = doc.read_text(encoding="utf-8")
    lines = raw.splitlines()
    tables, _ = parse_tables(lines)
    slugs = landed_slugs()
    hosts = landed_hosts()
    labels = landed_labels()

    records: list[dict] = []
    seen_ids: set[str] = set()
    excluded: list[dict] = []
    rows_converted = 0
    rows_excluded = 0
    tables_converted = 0

    for table in tables:
        spec = SPECS_BY_SIGNATURE.get(table.header)
        if spec is None:
            excluded.append(
                {
                    "header": " | ".join(table.header),
                    "rows": len(table.rows),
                    "line": table.line,
                    "reason": "表头签名未登记（非候选表或新表）",
                }
            )
            rows_excluded += len(table.rows)
            continue
        tables_converted += 1
        sec_rule = section_status_rule(table.section)
        for lineno, cells in table.rows:
            if len(cells) < len(table.header):
                cells = cells + [""] * (len(table.header) - len(cells))
            row = dict(zip(table.header, cells))
            name_raw = row.get(next((h for h, f in spec.mapping.items() if f == "name"), ""), "")
            name = clean_cell(name_raw)
            if not name or name in {"—", "-"}:
                excluded.append(
                    {
                        "header": " | ".join(table.header),
                        "rows": 1,
                        "line": lineno,
                        "reason": "行内无源名（表尾说明行）",
                    }
                )
                rows_excluded += 1
                continue

            rec: dict = {
                "id": slugify(name),
                "name": name,
                "doc_line": lineno,
                "section": table.section,
                "wave": wave_of(table.section, table.top),
                "needs_review": False,
            }
            if rec["id"] in seen_ids:
                # 同一源在多表重复出现：保留先出现的一条，重复条也留档并标待复核
                rec["id"] = f"{rec['id']}-{lineno}"
                rec["needs_review"] = True
            seen_ids.add(rec["id"])

            verticals: list[str] = []
            evidence_parts: list[str] = []
            verdict_raw = ""
            reach_raw = ""

            for header, fieldname in spec.mapping.items():
                value = clean_cell(row.get(header, ""))
                if not value or value in {"—", "-"}:
                    continue
                if fieldname == "vertical":
                    verticals.extend(
                        [v.strip() for v in re.split(r"[/、,，]", value) if v.strip()]
                    )
                elif fieldname == "auth":
                    kind, note = auth_kind(value)
                    rec["auth"] = {"kind": kind, **({"note": note} if note else {})}
                elif fieldname == "reach":
                    reach_raw = value
                elif fieldname == "cadence":
                    rec["cadence"] = value
                elif fieldname == "history_depth":
                    rec["history_depth"] = value
                elif fieldname == "anti_bot":
                    rec["anti_bot"] = value
                elif fieldname == "endpoint":
                    rec["endpoint"] = value
                elif fieldname == "cost":
                    rec["cost"] = value
                elif fieldname == "value":
                    rec["value"] = value
                elif fieldname == "verdict":
                    verdict_raw = value
                elif fieldname == "evidence":
                    evidence_parts.append(value)

            if verticals:
                rec["vertical"] = verticals
                # The original column is left byte-identical; these two are a
                # *reading* of it, not a rewrite. `vertical` mixes two orthogonal
                # dimensions (A–N are document sections = source class; the rest
                # are topics), so any statistic that grouped by it was mixing
                # two questions. See vertical-registry.json.
                classes, topics = split_verticals(verticals)
                if classes:
                    rec["source_class"] = classes
                if topics:
                    rec["topic"] = topics
                unknown = [v for v in verticals if v not in _REGISTRY_SINGLE
                           and v not in _REGISTRY_TOPICS]
                if unknown:
                    raise SystemExit(
                        f"vertical 取值未登记：{unknown}（候选 {rec.get('name')!r}）。"
                        "先在 vertical-registry.json 里登记；现场发明分类会让历史分组失去可比性"
                    )
            if evidence_parts:
                rec["evidence"] = {"summary": " / ".join(evidence_parts)}

            # --- 状态判定（只用文档已写下的列，不引入新判断） ---
            if spec.status_rule == "reach" and reach_raw:
                state, detail = reach_state(reach_raw)
                rec["reach"] = {"state": state, "detail": detail}
                if state == "direct_ok":
                    rec["status"] = "accepted"
                elif state == "blocked":
                    rec["status"] = "rejected"
                    rec["reason"] = (
                        f"实测不可达（{detail}）"
                        + (f"；反爬/阻断：{rec['anti_bot']}" if rec.get("anti_bot") else "")
                    )
                elif state == "mixed":
                    rec["status"] = "unknown"
                    rec["reason"] = f"可达性混合（{detail}）"
                    rec["needs_review"] = True
                else:
                    rec["status"] = "unknown"
                    rec["reason"] = f"可达性未判定（{detail or '空'}）"
                    rec["needs_review"] = True
            elif spec.status_rule == "verdict":
                state, reason = verdict_state(verdict_raw)
                rec["status"] = state
                if reason:
                    rec["reason"] = reason
                if state == "unknown":
                    rec["needs_review"] = True
                if reach_raw:
                    rstate, rdetail = reach_state(reach_raw)
                    rec["reach"] = {"state": rstate, "detail": rdetail}
            else:
                if sec_rule == "accept":
                    rec["status"] = "accepted"
                elif sec_rule == "candidate":
                    rec["status"] = "candidate_unprobed"
                elif sec_rule == "reject":
                    rec["status"] = "rejected"
                    rec["reason"] = f"章节判定为否决：{table.section}"
                else:
                    rec["status"] = "unknown"
                    rec["reason"] = f"章节未给判定：{table.section}"
                    rec["needs_review"] = True

            # --- 落仓对位（只在文档点名既有单元时填） ---
            row_text = " ".join(cells)
            slug, ambiguous = find_landed(row_text, slugs)
            if slug is None and not ambiguous:
                # 证据级对位：端点主机 == manifest 声明上游（不需要标待复核）
                host_hit = match_by_host(row_text, hosts)
                if host_hit:
                    slug = host_hit
            if slug is None and not ambiguous:
                # slug 词元对位（路径里的 shibor/shclearing 段；唯一命中才收）
                tok_hit = match_by_slug_token(row_text, slugs)
                if tok_hit:
                    slug = tok_hit
            if slug is None and not ambiguous:
                # label 对位：manifest 显示名 ↔ 行文本（证据级；唯一命中才收）
                lab_hit = match_by_label(rec["name"], row_text, labels)
                if lab_hit:
                    slug = lab_hit
            if slug is None and not ambiguous:
                # 低置信对位：名称归一。命中仍标待复核。
                guess = match_by_name(rec["name"], slugs)
                if guess:
                    slug = guess
                    rec["needs_review"] = True
            rec["landed_slug"] = slug
            if ambiguous:
                rec["needs_review"] = True
            # 注意：**不**因为"没对到单元"改写 status。status 只记文档给出的判定；
            # 落仓证据单列在 landed_slug。把「没对上」当成「未接入」也是一种编——
            # 文档没写单元名的已接源会被误算成待办，漏斗会永远清不掉。
            # needs_review = 「解析歧义」∪「accepted 且缺落仓出处」。
            # 后者实测终审仍有 3 条锚太短/中英断层机器判不了（LPR/上清所月报/星级季报），
            # 硬配会引入新错误形态；全部亮灯让人一眼扫过，漏斗单列计数不重复。
            if rec["status"] == "accepted" and rec.get("landed_slug") is None:
                rec["needs_review"] = True

            records.append(rec)
            rows_converted += 1

    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "schema": SCHEMA,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_doc": "data-source-scouting/INDUSTRY-DATA-SOURCES.md",
            "source_doc_sha256": sha,
            "generator": GENERATOR,
            "coverage": {
                "tables_converted": tables_converted,
                "tables_excluded": len([e for e in excluded if e["rows"] > 1]),
                "rows_converted": rows_converted,
                "rows_excluded": rows_excluded,
                "excluded_tables": [e for e in excluded if e["rows"] > 1],
            },
        },
        "candidates": records,
    }


def _name_key(name: str) -> str:
    """源名归一键：同一源会在多处表格出现（总表 + 欠账复测队列），必须能认成同一源。

    2026-11-11 实测教训：把「accepted 无证据」当待办清单时得到 99 条，其中 26 组的
    兄弟行**早就带着证据**（同一源在复测队列里测过）——不做归一会把重复 mention
    当成真空白，白跑一轮探测、还会往漏斗里塞重复行。
    """
    return re.sub(r"[\s\-_·（）()/]+", "", (name or "")).lower()


def summarize(doc: dict) -> str:
    cands = doc["candidates"]
    by_status: dict[str, int] = {}
    for c in cands:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
    landed = sum(1 for c in cands if c.get("landed_slug"))
    review = sum(1 for c in cands if c.get("needs_review"))
    cov = doc["meta"]["coverage"]

    # mention（每张表一行）与唯一源是两个口径：漏斗行数是 mention，业务上要的是唯一源。
    # 只报 mention 会被读成"有 199 个源"，实际只有 168 个。
    groups: dict[str, list[dict]] = {}
    for c in cands:
        groups.setdefault(_name_key(c["name"]), []).append(c)
    uniq = len(groups)
    acc_uniq = len({k for k, g in groups.items() if any(x["status"] == "accepted" for x in g)})
    # 真空白 = accepted、无证据、且同族无任何一行带证据。同族有证据的属于重复 mention。
    acked = [c for c in cands if c["status"] == "accepted"]
    no_ev = [c for c in acked if not c.get("evidence") and not c.get("landed_slug")]
    truly = [
        c for c in no_ev
        if not any(x.get("evidence") for x in groups[_name_key(c["name"])])
    ]
    dup_no_ev = len(no_ev) - len(truly)

    lines = [
        f"候选清单：{len(cands)} 条 mention / 唯一源 {uniq} 个（来源 {doc['meta']['source_doc']}）",
        f"  按状态（mention）：" + "，".join(f"{k}={v}" for k, v in sorted(by_status.items()))
        + f"；accepted 唯一源 {acc_uniq} 个",
        f"  已对到在产单元：" + str(landed) + "，待复核：" + str(review),
        f"  无证据且未落地：{len(no_ev)} 条 mention，其中**同族已带证据（重复 mention）** {dup_no_ev} 条"
        f" → **真空白 {len(truly)} 条**",
        f"  覆盖度：转换 {cov['tables_converted']} 表 / 排除 {cov['tables_excluded']} 表；"
        f"行 转换 {cov['rows_converted']} / 排除 {cov['rows_excluded']}",
    ]
    return "\n".join(lines)


def self_test() -> int:
    """把判定规则钉在样例行上——规则改了必须同时改这里。"""
    ok = True

    def check(label: str, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print(f"  FAIL {label}: got {got!r} want {want!r}")

    check("reach ✅", reach_state("✅200"), ("direct_ok", "✅200"))
    check("reach ❌", reach_state("❌**403**"), ("blocked", "❌403"))
    check("reach 混合", reach_state("混合"), ("mixed", "混合"))
    check("auth 无", auth_kind("无")[0], "none")
    check("auth free key", auth_kind("免费 key（全 census 查询强制 key）")[0], "free_key")
    check("auth appId", auth_kind("appId")[0], "unknown")
    check("verdict 接受", verdict_state("✅纳入")[0], "accepted")
    check("verdict 否决", verdict_state("放弃")[0], "rejected")
    check("verdict 空", verdict_state("")[0], "unknown")
    check("slug", slugify("**昆明市农业农村局·价格行情**"), "昆明市农业农村局-价格行情")
    check("section accept", section_status_rule("## 新增 ★接（15 个）"), "accept")
    check("section reject", section_status_rule("## 维持放弃（代理也救不了）"), "reject")
    check("section candidate", section_status_rule("## 备选"), "candidate")
    check("name match", match_by_name("UN Comtrade", {"un-comtrade": "un-comtrade"}), "un-comtrade")
    check("name match prefix", match_by_name("Eurostat", {"eurostat-api": "eurostat-api"}), "eurostat-api")
    check("name match short guard", match_by_name("data", {"data-x": "data-x"}), None)
    _h = {"www.nmc.cn": "nmc-weather", "data.mofcom.gov.cn": "mofcom-totalmonth"}
    check("host match", match_by_host("POST data.mofcom.gov.cn/datamofcom/front/totalmonth/query 免鉴权", _h), "mofcom-totalmonth")
    check("host full-token not suffix", match_by_host("x.mofcom.gov.cn/y", _h), None)
    check("host match ambiguous", match_by_host("www.nmc.cn 或 spb.gov.cn", _h), None)
    check("host no match", match_by_host("example.org/x", _h), None)
    _l = {"东财定期报告预约披露日历": "eastmoney-disclosure-plan", "文化和旅游部 国内居民出游数据": "mct-tourism-demand",
          "文化和旅游部 全国星级旅游饭店统计调查报告": "mct-star-hotel", "SHIBOR 报价与走势": "chinamoney-shibor"}
    check("label match zh short anchor", match_by_label("东财披露日历", "东财披露日历 | GET datacenter-web.eastmoney.com", _l), "eastmoney-disclosure-plan")
    check("label match zh tourism", match_by_label("文旅部·国内居民出游数据", "文旅部·国内居民出游数据 | zwgk.mct.gov.cn", _l), "mct-tourism-demand")
    check("label match shibor", match_by_label("Shibor", "Shibor | POST /ags/ms/cm-u-bk-shibor/ShiborHis", _l), "chinamoney-shibor")
    check("label too short", match_by_label("abc", "abc | x", _l), None)
    _s = {"chinamoney-shibor": "x", "chinamoney-lpr": "y", "shclearing-monthly": "z",
          "eastmoney-disclosure-plan": "w", "mct-star-hotel": "v", "mct-tourism-demand": "u"}
    check("slug token shibor", match_by_slug_token("POST /ags/ms/cm-u-bk-shibor/ShiborHis", _s), "chinamoney-shibor")
    check("slug token strong", match_by_slug_token("datacenter-web.eastmoney.com RPT_PUBLIC 披露日历", _s), "eastmoney-disclosure-plan")
    check("slug token shared host ambiguous", match_by_slug_token("chinamoney.com.cn 数据", _s), None)
    # 源名归一（2026-11-11 加）：漏斗行数是 mention，同一源会在总表与复测队列各出现一次。
    # 不算归一会把重复 mention 当成"真空白"去重跑探测（实测 29 → 7）。
    check("name key 全半角括号归一", _name_key("Expoflores（厄瓜多尔）"), _name_key("Expoflores (厄瓜多尔)"))
    check("name key 忽略大小写与空格", _name_key("KOSIS 零售/线上购物表"), _name_key("kosis零售线上购物表"))
    check("name key 仍区分不同源", _name_key("上清所月报") != _name_key("上清所 TRS 公告"), True)

    real = build()
    cov = real["meta"]["coverage"]
    if cov["rows_converted"] == 0:
        ok = False
        print("  FAIL 真实文档零转换")
    for c in real["candidates"]:
        if c["status"] in ("rejected", "unknown") and not c.get("reason"):
            ok = False
            print(f"  FAIL {c['id']} 缺 reason")

    # id 契约对位（2026-11-11 加）：schema 的 id.pattern 必须与 slugify 的真实产出兼容。
    # 事故：schema 写了 ASCII-only `^[a-z0-9][a-z0-9-]*$`，slugify 却保留中文
    # （`[^a-z0-9\u4e00-\u9fff-]` 才删），195 条里 119 条违约而无人察觉——两边各写
    # 一份真理、且从没跑过对方。现在每次 self-test 都拿真实产出过一遍 schema 的 id
    # 规则 + 唯一性，漂移当场红。
    id_pat = re.compile(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        ["properties"]["candidates"]["items"]["properties"]["id"]["pattern"]
    )
    seen_ids: set[str] = set()
    for c in real["candidates"]:
        cid = c["id"]
        if not id_pat.match(cid):
            ok = False
            print(f"  FAIL id {cid!r} 不匹配 schema pattern {id_pat.pattern}")
        if cid in seen_ids:
            ok = False
            print(f"  FAIL id 重复 {cid!r}")
        seen_ids.add(cid)
    print("self-test", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true", help="只打印清单，不写文件")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv[1:])

    if args.self_test:
        return self_test()

    doc = build()
    print(summarize(doc))
    if args.check:
        print("\n排除的表（未转换，逐条上报）:")
        for e in doc["meta"]["coverage"]["excluded_tables"]:
            print(f"  L{e['line']:>5} rows={e['rows']:>3}  {e['header'][:90]}")
        return 0

    Path(args.out).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

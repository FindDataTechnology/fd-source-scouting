# restaurant-rpi 侦察记录（NRA Restaurant Performance Index）

- 侦察日期：2026-11-07
- 侦察人：spider-heal batch agent（restaurant-rpi 建单随附）
- 结论：**可接，已生成单静默合入，待人工点亮**（spiders/restaurant-rpi/）

## 端点

| 端点 | 状态码 | 说明 |
|---|---|---|
| `https://restaurant.org/research-and-media/research/economists-notebook/additional-research/performance-index/`（工单 lead） | 404 | 旧链已死；404 页导航给出现行路径 |
| `https://restaurant.org/research-and-media/research/economists-notebook/restaurant-performance-index/` | 200 | 旧路径现名（与现行页同内容，88051 字节一致） |
| `https://restaurant.org/research-and-media/research/restaurant-economic-insights/restaurant-performance-index/` | 200 | **官方现行页**（页内正文 + 「Read the full RPI report」PDF 链接） |
| `https://restaurant.org/NRA/media/Research/RPI/2024/RPI-September-2026.pdf` | 200 | 当月 RPI 报告 PDF（647KB，3 页）= 结构化数据面；URL 规律 `/NRA/media/Research/RPI/2024/RPI-<Month>-<Year>.pdf`（目录段恒为 `2024`） |

## 直连/代理裁决

**直连通**（页面 2.1s / PDF 直连 200，全程未用代理）。spider 兜底：直连失败经
`http://127.0.0.1:7890` 重试一次，每 URL ≤2 次尝试、30s 超时。

## 鉴权

无。公开页面 + 公开 PDF，无 token/cookie/UA 门槛（普通浏览器 UA 即可）。

## 周期

月度。每月最后一个工作日发布（源文口径）；`data_period: month`。

## 历史深度（实测窗口）

- **spider 数据面 = 最新报告 PDF 第 3 页数据表，仅最近 5 个月滚动窗**
  （Sep-2026 版实测 2026-05 → 2026-09，5 个月 × 11 条序列）。
- **无 2007 年以来全史**。全史不在站上以结构化形态提供（页面正文仅当月叙述）。
- URL 规律探测（每 URL 单发一次）：`RPI-August-2026.pdf` 200、
  `RPI-December-2025.pdf` 200、`RPI-January-2020.pdf` 404、`RPI-March-2008.pdf` 404
  ——同目录至少回溯到 2025-12，未验证到头；**不做按月猜 URL 的回补**（无归档索引页，
  猜测式批量探测属 hammer）。若未来需要更深历史，须先找到官方归档索引页再议。

## 序列清单（11 条，Sep-2026 版实测值域 98.2–102.3）

RPI（总）；Current Situation Index + Same-Store Sales / Customer Traffic / Labor /
Capital Expenditures；Expectations Index + Same-Store Sales / Staffing / Capital
Expenditures / Business Conditions。中性 100（>100 扩张 / <100 收缩；非旧版 1995=100）。

## 接入成本

低。单页面 + 单 PDF 两跳，免鉴权，stdlib 可解（PDF 为 FlateDecode 文本流，按 Tm 坐标
聚类行 + x 间距合并单元格即可还原表格；共享 tabular 层不含 PDF，自实现约 200 行）。
解析结果对 Sep-2026 版逐格验证（5 行 × 11 列全对）+ golden 真实回放绿。

## 关键坑

1. **工单 lead 404**：RPI 现行页在 `restaurant-economic-insights/` 下（404 页导航可
   发现）；同内容旧路径 `economists-notebook/restaurant-performance-index/` 也活着，
   双页同字节。
2. **PDF 文本切块 + 同名双序列**：`100.7` 拆成 `100.`+`7`、`2026` 拆成 `20`+`2`+`6`，
   须坐标重建表格；Same-Store Sales / Capital Expenditures 在两节各一条，按
   「Current Situation Indicators: / Expectations Indicators:」分节落位 `cs_*`/`exp_*`。
3. **无全史 + golden 短寿命**：单版只有 5 个月窗，锚历史月的 golden 约 5 版后滑出窗口
   （约 2027-02 版起 2026-05 出窗），replay 失败属预期老化，重录即可——不是数据坏了。

## 首爬

2026-11-07 真实运行 `python3 spiders/restaurant-rpi/spider.py`：**5 行**
（2026-05…2026-09 × 11 列，样例行与逐格核对见 spiders/restaurant-rpi/README.md）。
交叉核对：2026-09 rpi=100.7 / current=100.7 / expectations=100.7 与官方页正文一致。

## 状态

**已接入 · 已点亮（2026-11-07 波1 收口）**

- 试跑：`run restaurant-rpi` success **5 行**（2026-05 → 2026-09，单版 5 个月滚动窗 × 11 字段）
- 点亮：`schedule: "41 5 2 * *"`（每月 2 日 05:41，取上月末版报告）
- 观测：**暂不入库**——库里只有 5 个观测月，低于 12 期门槛；抽取器
  `scripts/restaurant_extractors/restaurant_rpi.py` 每次运行显式留 SKIP 说明，
  月频运行自然攒期，攒到 12 期起按 short_window(12-23) 自动放行（不拿 5 个点充趋势）
- 口径守卫：golden 001 replay ok=True（rows=5）
- lints：validate_manifests / check_manifest_commands / conformance_gate 对本单元 0 violations

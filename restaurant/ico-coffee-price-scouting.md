# ico-coffee-price 侦察记录（ICO 咖啡指标价格）

- 日期：2026-11-07
- 侦察人：spider 生成单（ico-coffee-price）
- 结论：**已建单元** `fd-industry-data/spiders/ico-coffee-price/`，生成单静默合入，待人工点亮

## 端点与状态（全部 2026-11-07 实测）

| 端点 | 状态 | 说明 |
|---|---|---|
| `GET https://data.ico.org/globe/api/v1/globe/icip` | **200，采用（主）** | 日度 ICIP 宽表 JSON，~35 KB；`daily[]`（date/ICIP/COL_MILDS/OTH_MILDS/BRA_NAT/ROBUSTAS/NY_ARABICA/LDN_ROBUSTA/pct）+ `units` + `range` + `entitlement` |
| `GET https://data.ico.org/globe/api/v1/globe/icip/history` | **200，采用（备）** | 同窗口列式形态 `columns/rows`（多 NY_2ND3RD/LDN_2ND3RD 期货列）；主路径失败兜底 |
| `GET https://data.ico.org/globe/api/v1/meta` | 200 | 门户元数据：`entitlement.gating=true`、`analytical.icip_daily_prices=true`、trade 流 1963–2026 |
| `GET https://data.ico.org/globe/data/snapshots/icip.json` | **403** | 静态快照对匿名关闭（Apache 403，带 Referer 亦拒） |
| `https://www.ico.org/new_historical.asp` | **404** | 旧站历史数据页已随迁移消失（302 → ico.org 后 404） |
| `https://ico.org/resources/public-market-information/` | 200（页面） | 旧站公共市场信息页：仅挂月度 I-CIP PDF（`documents/prices/I-CIP_MM.YYYY.pdf`，实测 2025-12 起在挂；2023 及更早全 404，icocoffee.org 旧档同样 404） |
| `https://ico.org/documents/prices/I-CIP_09.2026.pdf` | 200 | 月度 PDF 实测：每日 5 指标表（I-CIP + 4 组指标，US cents/lb）+ Average/High/Low，文本层规整；但镜像无 PDF 解析库（pypdf/pdfplumber 均未预装），不接 |
| Excel 下载 | **不存在公开链路** | 页面明文：「available in an excel format **on request** from stats@ico.org」（Members/学术免费，其余报价） |
| `https://ico.org/resources/coffee-market-report-statistics-section/` | 200 | 月度 Coffee Market Report PDF（cmr-*.pdf），价格表在 PDF 内，同上不接 |

## 直连/代理裁决

- **直连可达**：data.ico.org 与 ico.org 全部端点直连 HTTP 200（本机，2026-11-07），未触发代理回退。
- spider 行为：直连优先（显式禁用环境代理，行为确定）→ 失败回退一次 `http://127.0.0.1:7890`；超时 30s。
- 无鉴权、单端点、月度刷新级低频，不做频次对抗/指纹伪装。

## 鉴权

- 匿名即取（`tier: anonymous`）。ICIP 载荷 `entitlement`: `{"openFrom": "2026-01-01", "note": "Prices from 2026 are open to everyone. Sign in for the full series."}`。
- 完整数十年序列需门户注册登录（付费订阅）；meta 中 `freeYear: 2025` 暗示逐步放开年份，未来可能自然扩窗。

## 周期与历史深度（真实观测窗口）

- **周期：日度**（交易日逐日一行；停市日无行，如周末与假日）。
- **实测窗口：2026-01-02 → 2026-11-05，217 个交易日**（全量 1085 行 = 217 日 × 5 指标）。
- ICO 官方指标自 1989 年起有公开序列，但均在订阅墙内——**本单元不伪造更早历史**，匿名窗口内有多少取多少。

## 接入成本

- 低：单端点 JSON GET、免鉴权、纯标准库解析（urllib/json/re），无新依赖。
- 行模型：宽表转长表（date, indicator, price, unit），同 fao-food-price 约定；`limit` 按字典序 earliest-first 截断。
- 取 ICO 五条官方指标；`NY_ARABICA`/`LDN_ROBUSTA`（ICE 期货参考价）与 `pct`（日涨跌幅）不取。

## 关键坑

1. **无公开 CSV/Excel**：工单预期的「CSV/Excel 下载」在新旧两站均已不存在——旧历史页 404，Excel 明文 on-request。实际最佳公开数据面是门户 JSON API（结构化优于 CSV，工单精神内）。
2. **匿名窗口窄且会动**：ICIP 只开放 2026-01-01 起；meta `freeYear:2025` 与载荷 `openFrom:2026-01-01` 并存，放开节奏由 ICO 运营决定，窗口非契约。深历史扩窗需门户凭据（登录会话），可作后续可选项。
3. **当月值日内修订**：月度 PDF 明注日间修订（「I-CIP for 25-Sep has been revised」）；当月/最新交易日值不可作 golden 锚——本单元锚窗口起点 2026-01-02（I-CIP=297.71，深历史）。

## 首爬样例（2026-11-07 冒烟，`limit=24` 重放 24 行；全量 1085 行）

```json
{"date": "2026-01-02", "indicator": "I-CIP", "price": 297.71, "unit": "US cents/lb", "source": "ico-coffee-price"}
{"date": "2026-01-02", "indicator": "Colombian Milds", "price": 371.34, "unit": "US cents/lb", "source": "ico-coffee-price"}
{"date": "2026-01-02", "indicator": "Other Milds", "price": 370.32, "unit": "US cents/lb", "source": "ico-coffee-price"}
{"date": "2026-01-02", "indicator": "Brazilian Naturals", "price": 347.67, "unit": "US cents/lb", "source": "ico-coffee-price"}
{"date": "2026-01-02", "indicator": "Robustas", "price": 187.78, "unit": "US cents/lb", "source": "ico-coffee-price"}
```

最新交易日样例（2026-11-05）：I-CIP 247.74 / Colombian Milds 337.37 / Other Milds 317.92 / Brazilian Naturals 277.49 / Robustas 157.7。

## 状态

**已接入 · 已点亮（2026-11-07 波1 收口）**

- 试跑：`run ico-coffee-price` success **285 行**（2025-09-01 → 2026-11-05 交易日宽表）
- 点亮：`schedule: "23 6 * * *"`（每日 06:23；当月活文档 + 近 14 个归档月）
- 观测：5 条概念各 285 期入库（`price.coffee.{icip,colombian_milds,other_milds,brazilian_naturals,robustas}.daily`，unit=us_cents_lb，entity WORLD(300932)），过命名门 verified
- 口径守卫：golden 001 按真实宽表形态重锚后 replay ok=True（旧 golden 是长表 `date/indicator/price` 形态，已废弃）；列交叉校验按可辩护不变量收紧（Robustas 最低 + I-CIP 落四组值域；**去掉**「Colombian 必最高」——实测 2026-04-07 Other Milds 更高）
- 拦截记录：上述校验修正前，`months_back=14` 试跑在 2026-04-07 整月判红；修正后同参数 success
自检：golden schema + 锚重放 GREEN（fd_industry_data.health.samples / loader）；
仓级 validate_manifests / check_manifest_commands / conformance_gate 对本单元全绿
（仓内 restaurant-rpi、education_card_catalog 两处他人单元的既有红与本单元无关）。

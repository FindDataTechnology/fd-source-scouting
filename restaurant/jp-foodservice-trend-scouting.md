# 日本外食 — JF 外食産業市場動向調査（领域侦察 + 接入记录）

- 侦察日期：2026-11-07（首轮）/ 2026-11-08（接入与实证）
- 归属：`add-restaurant-vertical` 波1 日本腿（用户 2026-11-07 裁决「日本：再深挖一轮」）
- 结论：**已接入·已点亮**（单元 `spiders/jp-foodservice-trend/`）

## 1. 端点

| 项 | 实测值 |
|---|---|
| 主体 | 一般社団法人 日本フードサービス協会（JF） |
| 索引页 | `https://www.jfnet.or.jp/industry_report/`（分页，可回溯到 ~2020） |
| 数据文件 | 月次 Excel：`/wp/wp-content/uploads/<YYYY>/<MM>/data_c_m<YYYY>_<M>.xls` |
| 鉴权 | 无（公开静态文件） |
| 直连/代理 | 直连可达（本机与生产集群均可，无需代理） |
| 周期 | 月（每月初发布上月数据；本机实测 2026-11-08 时最新完整版为 2026-09） |
| 历史深度 | 单版报告内 13 个月滚动窗；索引分页回溯可到 ~2020（本单元 `since` 参数按需回溯） |
| 单版体量 | 7 个业态 × 13 个月 × 4 指标 |

## 2. 口径（易错点逐条）

- **前年同月比**（对上年同月之比），`1.0 = 持平`。不是百分比变化，也不是指数点位 —— 观测单位写 `ratio_yoy`，避免把 1.0765 读成 7.65。
- **全店基准**（全店 sheet，含新开店），非同店。与同店销售（same-store sales）不可比。
- 四个指标：`a. 売上高` / `b. 店舗数` / `c. 利用客数` / `d. 客単価`。
- 业态七行：全体 / ファーストフード / ファミリーレストラン / パブレストラン・居酒屋 / ディナーレストラン / 喫茶 / その他。
- 观测自然键无「业态」列 → 业态落在实体上（`entity_type='industry'`，`code=jp.foodservice.*`，见 `scripts/register_jp_foodservice_segments.py`）。不这么做会让每月 7 行撞同一自然键、被 `ON CONFLICT DO NOTHING` 静默吞掉 6 行。
- 滚动窗重叠月取最新 `scraped_at`；payload 的 `edition` 只作溯源，不当观测日期。

## 3. 接入实证（2026-11-08）

| 步骤 | 命令 | 结果 |
|---|---|---|
| 落库 | `fd-runner jp-foodservice-trend --limit 500 --params '{"since":"2025-01"}'` | success，147 行原始 payload，21 份月次报告（2025-01…2026-09），69.2s |
| 观测 | `scripts/extract_restaurant_wave0.py --only jp-foodservice-trend` | **588 行入库**（21 期 × 7 业态 × 4 指标） |
| 命名门 | `scripts/naming_gate_restaurant.py --apply` | 4/4 concepts + registry 双置 verified，带 `short_window(21)` 声明 |
| golden | `golden/001-jp-foodservice-trend.json` | 锚 2025-01／全体 四个值；`replay_sample` ok、`validate_sample` 无错 |
| conformance | `/usr/bin/python3 scripts/conformance_gate.py` | PASS（本单元零违规） |

## 4. 坑位

- **索引页解析**：报告链接分散在分页索引里，且上传目录按「年/月」分层（2026-01 版落在 `uploads/2026/02/`），不能按数据月拼路径。
- **Excel 不是 xlsx**：是 BIFF `.xls`，需 `xlrd`（openpyxl 读不了）。
- **`since` 与缺省行为不同**：缺省只取索引第 1 页（最新 ~9 份报告、合并约 21 个月）；给 `since` 会逐页回溯并下载覆盖该月起点的所有报告，耗时随回溯深度线性增长（回溯到 2025-01 = 21 份 ≈ 70s）。
- **末月会修订**：滚动窗最新 1-2 个月在下版报告里可能被改写，golden 锚在历史定稿月（2025-01）而非末月。

## 5. 挂账

- 无 EDINET 类鉴权依赖（本单元只吃 JF 公开 Excel）。日股**公司披露**车道（EDINET API v2）是另一条线，key 未到位，见 `add-restaurant-vertical` 任务 3.4。
- 业态口径若上游调整名称（如「パブレストラン/居酒屋」拆行），`SEGMENT_CODE` 映射会失配 → 抽取器按「未识别业态」计数并写进 notes，不会静默丢。

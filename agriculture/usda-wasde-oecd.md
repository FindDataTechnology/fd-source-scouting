# usda-wasde-oecd 侦察报告

侦察时间：2026-11-08（本机直连海外，未用代理；代理 7890/7892 实测不可用）
有效 HTTP 请求：11 次（WASDE 7、OECD 4）。超预算原因：Nov 期文件未发布，浪费 3 次尝试。

## 结论（两行）

1. **WASDE：可接入（表格文件）** — 官方索引页列出每期 `.pdf/.txt/.xls/.xml` 四种同源下载，`.xls` 为真表格（`application/vnd.ms-excel`），`.txt` 为定宽全文。当前最新可用期 = **wasde1026（WASDE-676, October 2026）**。
2. **OECD-FAO Outlook：直连不可得** — `agri-outlook.org` 与 `oecd.org` 三个页面全部 **403**；OECD SDMX API 可达（5.96MB 数据结构正常返回）但未找到 Outlook 数据流 id，csv 直链与是否需要 key **未验证**。

## 探测记录

| # | URL | 方法 | 状态码 | 大小 | content-type | 判定 |
|---|---|---|---|---|---|---|
| 1 | `https://usda.gov/oce/commodity/wasde/` | GET -L | 200（跳转后） | 159,713 | text/html | 索引页可达，落地 `/about-usda/.../wasde-report` |
| 2 | 同上（取 href 列表） | GET | 200 | — | text/html | 含 1026/1126 两期 × 4 后缀直链 |
| 3 | `.../wasde/wasde1126.txt` | GET -L | **200（实为 apology 页）** | 369 | text/html | 未发布，陷阱见「坑位」 |
| 4 | `.../wasde/wasde1126.xls` | GET -L | **200（apology）** | 369 | text/html | 未发布 |
| 5 | `.../wasde/wasde1126.xml` | GET -L | **200（apology）** | 369 | text/html | 未发布 |
| 6 | `.../wasde/wasde1026.txt` | GET -L | 200 | 122,378 | text/plain | **可用**，定宽全文 |
| 7 | `.../wasde/wasde1026.xls` | GET -L | 200 | 354,304 | application/vnd.ms-excel | **可用**，多 sheet 表格 |
| 8 | `https://www.agri-outlook.org/` | GET -L | 403 | 5,421 | text/html | 被挡（疑 Cloudflare/地域） |
| 9 | `https://www.oecd.org/en/topics/sub-issues/agricultural-outlook.html` | GET -L | 403 | 5,573 | text/html | 被挡 |
| 10 | `https://www.oecd.org/en/data/datasets/oecd-fao-agricultural-outlook.html` | GET -L | 403 | 5,588 | text/html | 被挡 |
| 11 | `https://sdmx.oecd.org/public/rest/v1/dataflow/all/all/latest` | GET + `Accept: application/vnd.sdmx.structure+json` | 200 | 5,958,393 | JSON | **API 活**；grep `AGROUT/AGRI_OUTLOOK/AGLINK` 无命中 |

补充：`dataflow?format=jsondata`（不带正确 Accept）= **406 / 111B / text/plain**，说明服务在但拒绝该 Accept。

## WASDE 通道

- **数据形态**：四件套同源同 slug，任选：
  - `.xls` 354 KB —— **首选**，真表格（多 sheet，供需平衡表按商品分组）
  - `.txt` 122 KB —— 定宽文本，前 30 行是表头+列宽约定，可切列解析
  - `.pdf`/`.xml` —— 索引页给出链接；`.xml` 内容结构**未验证**（1126 未发布，未取到 1026 的 xml）
- **直链 URL 模板**（已验证 1026）：
  - `https://www.usda.gov/oce/commodity/wasde/wasde{MM}{YY}.xls`
  - `https://www.usda.gov/oce/commodity/wasde/wasde{MM}{YY}.txt`
  - 文件名 = `wasde` + 两位月 + 两位年（`1026`=2026-10，`1126`=2026-11）
- **更新节奏**：月度。索引页同时列出相邻两期（1026 与 1126），编号 WASDE-676 连续递增。
- **可回溯期数**：索引页含 `historical-wasde-report-data` 入口（`/oce/commodity-markets/wasde/historical-wasde-report-data`），最早期数**未验证**（未抓取该页）。
- **反爬/额度**：无 key、无登录、无 UA 校验（默认 curl UA 即 200）。

## OECD-FAO 通道

- **网页侧全 403**：`agri-outlook.org`、`oecd.org` 的 topic 页与 dataset 页三个入口均 403，正文仅 5.4–5.6 KB（挑战页），未见内容。
- **SDMX API 侧可达**：`sdmx.oecd.org/public/rest/v1/` 对正确 `Accept` 返回 200 与 5.96 MB 数据结构 JSON，说明**限制在网页/WAF 层，不在 API 层**。
- **数据流定位未成功**：在该全量 dataflow 列表里，`AGROUT`/`AGRI_OUTLOOK`/`AGLINK` 均无命中（可能 id 命名不同，如 `DSD_AGROUT`，或该数据集不走 SDMX dataflow 而走 data-explorer 静态文件）。**需 key 与否、csv 直链是否存在：未验证**。
- **形态判断**：惯例上是「年度基线报告 PDF + 数据附件（csv/xlsx）」双轨，但本轮**未拿到任何 CSV/统计直链证据**，故不作断言。
- **更新节奏**：年度（公开印象），本轮**未从响应中验证**。

## 坑位

1. **200-OK 陷阱（最重要）**：文件名猜错/尚未发布时，USDA 不返回 404，而是返回 200 + `text/html` 369 字节的 apology 页，落地 URL 变成 `https://www.usda.gov/please_wait/apology.htm`。文本："This file is not yet available. Please check back after the scheduled release date/time." → 采集器必须校验 `content-type` 与 `size`，不能只看状态码。今天是 11-08，Nov 期尚未发布。
2. **跟随跳转**：`usda.gov/oce/commodity/wasde/` 会被重写到 `/about-usda/.../wasde-report`，代码里请直接用落地 URL 或允许 -L。
3. **OECD 403 是 WAF 层**：同一台机器访问 `sdmx.oecd.org` 正常，(www.)oecd.org 全 403 —— 不要重试网页，改走 API 或换出口。
4. **不要写死"最新期"**：期号由发布时间决定，必须从索引页解析 href 决定，别用当前月份推算（1126 就是反例）。
5. **无 CSV 证据别假设 CSV**：OECD 侧本轮零表格证据。

## 建议

- WASDE 按「表格文件」接入：`wasde{MM}{YY}.xls`，用索引页 `href` 发现新期；`.txt` 作交叉校验/兜底。加 `content-type=application/vnd.ms-excel` 且 `size>100KB` 双校验，规避 apology 页。
- 回溯补一条探测：`historical-wasde-report-data` 页，确认最早年份与是否同样四件套（本轮未做）。
- OECD-FAO 暂标 **blocked-by-403**，Unit 结论「不可得（直连）」；若要继续，唯一有希望的路径是 SDMX：用正确 `Accept: application/vnd.sdmx.structure+json` 拉 `dataflow` 全表后按 name 含 "Agricultural Outlook" 过滤（本轮只 grep 了 id 关键词，未按 name 过滤）。
- 与既有单元的关系：WASDE 的 `.xls` 供给出平衡表口径；`usda-psd`（api.fas.usda.gov）是另一套库，勿混用同一期号。

## 证据（实际响应片段）

`wasde1026.txt` 首行（HTTP 200, text/plain, 122,378 B）：

```
                                WASDE - 676 - 8                      October 2026
```

第 3–5 行：

```
                  World and U.S. Supply and Use for Grains  1/
                              Million Metric Tons
```

# nbs-agri 侦察报告

侦察时间：2026-11-08（直连，`curl --noproxy '*'`，未登录、未绕反爬）
结论先行：**easyquery 在本机网络被 WAF 全面拒绝（4 次探测全 403 UrlACL），农业指标 code 无法实测确认**；
可用的农业数据只能从 `www.stats.gov.cn` 的《中国统计年鉴》取，且**只有 JPG 表格图片，无 HTML 表格**。

## 既有单元现状

单元：`fd-industry-data/spiders/nbs-stats/`（`spider.py` + `manifest.yaml` + README）

- 端点：`https://data.stats.gov.cn/easyquery.htm`，`Referer: .../easyquery.htm?cn=A01`
- 取数 URL 形态（`spider.py:121-134` `_build_nbs_url`）：

```
{NBS_BASE_URL}?m=QueryData&dbcode={dbcode}&rowcode=zb&colcode=sj
 &wds=[] &dfwds=[{"wdcode":"zb","valuecode":"<zbcode>"},{"wdcode":"sj","valuecode":"<起始期>"}]
 &k1=<毫秒时间戳>
```

- 既有 (dbcode, zbcode) 映射（`INDICATOR_CATEGORIES`，`spider.py:52-72`）：

| 类别 | dbcode | zbcode | 频率 | 起始期拼法 |
|---|---|---|---|---|
| GDP 季度 | hgjd | A0201 | Q | `YYYYA` |
| GDP 年度 | hgnd | A0201 | A | `YYYY` |
| GDP 分省 | fsjd | A0201 | Q | `YYYYA` |
| CPI | hgyd | A0901 | M | `YYYY01` |
| PPI | hgyd | A0902 | M | `YYYY01` |
| 工业生产 | hgyd | A0202 | M | `YYYY01` |
| PMI | hgyd | A0M01 | M | `YYYY01` |
| 人口 | hgnd | A0301 | A | `YYYY` |
| 就业 | hgyd | A0302 | M | `YYYY01` |

- 解析：`returndata.datanodes[].code` 形如 `<zbcode>.<period>`，`data.strdata` 取值；
  名称从 `returndata.wdnodes`（wdcode=`zb`/`sj`）反查。**扩指标只需给新的 zbcode，解析器零改动。**
- 已知坑（manifest 已记）：`data.stats.gov.cn` 对部分出口段 WAF 403，生产 tencent 站正常。

## 探测记录

| # | URL | 状态码 | 大小 | 判定 |
|---|---|---|---|---|
| P1 | `data.stats.gov.cn/easyquery.htm?m=QueryData&dbcode=hgyd&zbcode=A0901&sj=202601`（IPv6） | 403 | 315B | WAF `reason:UrlACL`，非登录墙 |
| P1b | 同 P1，强制 IPv4（出口 122.190.204.82） | 403 | 293B | 家宽 v4/v6 双双被拦 |
| P2 | 同主机 `m=getTree&dbcode=hgnd&wdcode=zb&id=zb` | 403 | 315B | 非路径级放行，整站 ACL |
| P3 | `www.stats.gov.cn/sj/ndsj/` | 200 | 79,379B | 年鉴总入口可达 |
| P4 | `www.stats.gov.cn/sj/ndsj/2025/indexch.htm` | 200 | 887B | frameset（gb2312），入口 `left.htm` |
| P5 | `www.stats.gov.cn/sj/ndsj/2025/left.htm` | 200 | 59,351B | 章节导航，第十二章「农业」 |
| P6 | `.../2025/html/C12-02.htm`、`C12-08.htm` | 404 | 555B | **无 HTML 版表格**，只有 .jpg |
| P7 | `.../2025/html/C12-02.jpg`、`C12-01.jpg` | 200 | 347,259B / 203,182B | 表格图片，可直接读值 |
| P8 | `.../2025/html/C03-06.jpg`（分行业增加值） | 200 | 124,394B | 表格图片，含农林牧渔业 |

总探测点 8（P1 计 2 次尝试），实际耗时约 4 分钟。

## 可用指标清单

指标 code 一栏**全部为「未获取」**——easyquery 403，无任何真实响应可据以填码，
按纪律不猜（`A0D0x` 之类凭记忆写码一律不采用）。
下列中文名/期数/数值均来自《中国统计年鉴 2025》JPG 表格的**实际读取**，非记忆。

| 指标（年鉴表号） | 频次 | 最新期 | 最新值 | 历史深度 |
|---|---|---|---|---|
| 粮食产量（12-2，万吨） | 年 | 2024 | **70,649.9** | 表内 2019–2024（逐个年鉴回溯可到 1949） |
| 谷物产量（12-2，万吨） | 年 | 2024 | 65,228.7 | 同上 |
| 稻谷 / 小麦 / 玉米（12-2，万吨） | 年 | 2024 | 20,753.5 / 14,009.9 / 29,491.7 | 同上 |
| 大豆产量（12-2，万吨） | 年 | 2024 | 2,064.8 | 同上 |
| 农作物总播种面积（12-1，千公顷） | 年 | 2024 | **173,000** | 表内 2000/2010/2015/2020/2023/2024 |
| 粮食播种面积（12-1，千公顷） | 年 | 2024 | **119,319** | 同上 |
| 稻谷/小麦/玉米/大豆播种面积（12-1，千公顷） | 年 | 2024 | 29,007 / 23,587 / 44,741 / 10,325 | 同上 |
| 农林牧渔业增加值（3-6，亿元，当年价） | 年 | 2023 | **93,967.0** | 表内 2020–2023（2024 未出） |
| 猪年末头数（存栏，12-2，万头） | 年 | 2024 | **42,742.9** | 2019–2024 |
| 肉猪出栏头数（12-2，万头） | 年 | 2024 | **70,256.3** | 2019–2024 |
| 肉类总产量 / 猪肉（12-2，万吨） | 年 | 2024 | 9,779.9 / 5,706.0 | 2019–2024 |
| 农林牧渔业总产值及指数（12-3） | 年 | 2024 | 未读（预算用尽） | 表在，未取 |
| 牲畜饲养情况（12-13）、畜产品产量（12-14） | 年 | 2024 | 未读 | 表在，未取 |

频次判定：**只有年度**。年鉴 12-x 与 3-6 均为年度表；
粮食/播种面积/存栏出栏的季度或月度口径在 NBS 季度新闻发布中存在，
但 easyquery 是否单列序列**本次无法验证**（403）。

## 坑位

1. **easyquery 在本机不可用**：`data.stats.gov.cn` 全站 UrlACL 403，IPv4/IPv6 均中招，
   `QueryData` 与 `getTree` 两条路径一样。不是限流、不是 UA/Referer 问题，重试无意义。
   → 任何"凭本机实测 easyquery 拿到农业 code"的结论都不可能成立，必须到生产（tencent 站）验。
2. **年鉴只有图片**：2025 版 `html/C12-01.jpg`…`C12-17.jpg` 是扫描/排版图，
   `C12-xx.htm` 全部 404。要机器可读必须走视觉/OCR，或另找源（如分省年鉴、CASDE）。
3. **年鉴与增加值表不同步**：12-x 已到 2024，3-6 分行业增加值只到 2023（最终核实滞后）。
4. **编码体系两套**：年鉴表号（12-2 / 3-6）与 easyquery zbcode（如 A0201）完全不同名，
   不可互相推算；`fd-data-quality/scripts/_nbs_client.py` 的 `CURATED_INDICATORS` 里
   也没有任何农业 zbcode（只有 A0201 GDP、A0D01 货币供应量等）。
5. **年份列不是连续年**：12-1 是 2000/2010/2015/2020/2023/2024 六个跳点年，
   不是逐年；12-2 是 2019–2024 逐年。按"每年一行"入库会踩空。

## 建议

**判断：需新端点 + 部分不可得。**

1. **code 必须到生产环境补测**（本机不可得）。方法固定、代价极小：
   `m=getTree&dbcode=hgnd&wdcode=zb&id=zb` 取年度指标树 → 找「农业」节点 →
   其子节点 code 即 zbcode → `QueryData` 验证。既有 `_build_nbs_url` 与解析器**零改动**，
   扩指标只是往 `INDICATOR_CATEGORIES` 加 `"agriculture": {"annual": {"dbcode":"hgnd","zbcode":"<实测>","freq":"A"}}`。
   在 code 落袋前，**不要**在 `manifest.yaml` 写任何农业指标（会变成未验证断言）。
2. **本机可立即落地的只有年鉴路线**，但它是图片：若接受视觉/OCR，
   `C12-01/12-02/12-13` 三张图就能覆盖粮食产量、播种面积、存栏出栏；
   否则建议改投 MOA（`www.moa.gov.cn` 同站已可达）或 CASDE。
3. **别把年鉴表号当 code 用**。两套体系不通用，混用会在 fd-runner 里静默取空。
4. **优先补测项**：粮食产量（年度核心）、粮食播种面积、猪年末头数、肉猪出栏头数、
   农林牧渔业增加值（注意增加值在 easyquery 里可能挂在 GDP 树 A0201 子节点下，而非农业树）。
5. **生猪月度/季度**（能繁母猪存栏等）大概率不在 easyquery，建议按 `INDUSTRY-DATA-SOURCES.md`
   既有判断走 MOA 生猪产能单元，不要硬塞进 nbs-stats。

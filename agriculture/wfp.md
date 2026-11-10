# wfp 侦察报告

侦察时间：2026-11-07（UTC 探测）｜执行：只读 HTTP 探测，8 个探测点，无代理直连

## 既有单元现状

目录 `fd-industry-data/spiders/wfp-food-price/`，`manifest.yaml` 里 `parked: true`，无 `schedule`。

| 项 | 值 |
|---|---|
| 入口 | `run_wfp_food_price(limit=100)`，仅标准库 urllib/json/csv |
| 元信息端点 | `GET https://data.humdata.org/api/3/action/package_show?id=wfp-food-prices`（slug 运行时解析，不硬编码） |
| 资源 | CSV，`resource 12d7c8e3-eff9-4db0-93b7-726825c4fe9a`（dataset `4fdcd4dc-5c2f-43af-a1e4-93c9b6539a27`），`wfpvam_foodprices.csv`，225,787,557 B |
| 字段 | 输入 `adm0_name/mkt_name/cm_name/mp_year/mp_month/mp_price/cur_name/um_name` → 输出 `country/market/commodity/month(YYYY-MM)/price/currency/unit/url/source/scraped_at` |
| golden | `golden/001-wfp-food-price.json`，锚 Afghanistan/Fayzabad/Bread - Retail/2014-01/50.0/AFN |

**为什么被 park**（`fd-industry-data/output/adjudication/cases/wfp-food-price.md`）：2026-11-06 全舰队基线实跑失败，报「表头异常（无 adm0_name 列）」；当时实探 HDX 现行资源返回 **HTTP 202 + 空 body**（重试 / Range / `?download=1` 全 202），叠加该数据集 2021-08 后冻结。裁决三选项取 park（保留单元与历史 payload，上下游恢复即可 repair）。附带事实：semantic_observations 中 wfp 行数 = 0，从未供数。

## 探测记录

| # | URL | 状态码 | 大小 | content-type | 判定 |
|---|---|---|---|---|---|
| 1 | `/api/3/action/package_show?id=wfp-food-prices` | 200 | 18,531 | `application/json;charset=utf-8` | 旧数据集仍注册，自述「This no longer updated dataset」 |
| 2 | 旧资源 `.../12d7c8e3-.../download/wfpvam_foodprices.csv`（不跟跳转） | 302 | 1,507 | `text/html` | 正常 HDX 签名 S3 跳转，非封禁 |
| 3 | 同上，`-L` + `Range: 0-4095` | **206** | 4,096 | `text/csv` | **可读**。2026-11-06 的「202 空体」当前不可复现（瞬态/未跟跳转） |
| 4 | `/api/3/action/package_search?q=food prices&rows=15` | 200 | 260,425 | json | 命中 3298，前 15 全是 FEWS NET/IFPRI，需换检索轴 |
| 5 | `package_search?fq=organization:wfp&rows=40` | 409 → 200 | 923 → 1,884,985 | json | 首次 `sort=dataset_date` 被 Solr 拒（SpatialField 不可排序），改 `metadata_modified` 成功；**发现 `global-wfp-food-prices`** |
| 6 | `package_show?id=global-wfp-food-prices` | 200 | 722,689 | json | **现行数据集**，40 个按年 CSV，last_modified 2026-11-05 |
| 7 | 新资源 `502190c6-.../wfp_food_prices_global_2026.csv`，`Range: 0-262143` | 206 | 262,144 | `text/csv` | 可读，真实表头 + 数据（首次按猜测路径 `global-wfp-food-prices-2026.csv` 试得 404/349B，改用 API 给出的 url） |
| 8 | 同上，`Range: -524288`（尾段） | 206 | 524,288 | `text/csv` | 可读，尾部最大观测日 **2026-10-15** |

无 5MB 以上落地；无重试放大；无反爬交互。

## 活性判定

**旧数据集 `wfp-food-prices`（manifest 当前指向）——已冻结**

- `last_modified` = **2021-08-22T08:27:33.221716**（资源级同值）
- `metadata_modified` = 2026-04-27T13:03:05（仅元数据被后台动过，资源未变）
- `dataset_date` = `[1990-01-01 TO 2021-08-15]`
- 资源 `size` = 225,787,557 B；按采样均行长 99.9 B 估算 **≈ 226 万行**
- 数据最新期：**2021-08**（文件可下载，但内容不再增长）

**新数据集 `global-wfp-food-prices`（活跃）**

- `last_modified` = **2026-11-05T22:17:14.214765**（距今 2 天），`metadata_modified` 同
- `dataset_date` = `[1990-01-15 TO 2026-11-15]`，`data_update_frequency` = 30（月）
- `metadata_created` = 2021-08-27（旧集冻结后 5 天接续上线）
- 40 个按年 CSV，合计 **620.9 MB**；2026 分片 42,061,301 B
- 实测数据最新期：**2026-10-15**；2026 分片按均行 128.8 B 估算 **≈ 33 万行**，全库 **≈ 480 万行**
- 覆盖 98 国 / 约 3000 市场，许可 CC BY-IGO

## 真实样例

旧库（探测 3，`Range 0-4095` 头部，原始 18 列）：

```csv
adm0_id,adm0_name,adm1_id,adm1_name,mkt_id,mkt_name,cm_id,cm_name,cur_id,cur_name,pt_id,pt_name,um_id,um_name,mp_month,mp_year,mp_price,mp_commoditysource
1.0,Afghanistan,272,Badakhshan,266,Fayzabad,55,Bread - Retail,0.0,AFN,15,Retail,5,KG,1,2014,50.0,
```

新库（探测 7/8，17 列）：

```csv
countryiso3,date,admin1,admin2,market,market_id,latitude,longitude,category,commodity,commodity_id,unit,priceflag,pricetype,currency,price,usdprice
AFG,2026-05-15,Badakhshan,Argo,Badakhshan,3690,37.04,70.46,cereals and tubers,Bread,55,KG,actual,Retail,AFN,77,1.2
AFG,2026-05-15,Badakhshan,Argo,Badakhshan,3690,37.04,70.46,cereals and tubers,Wheat,84,KG,actual,Retail,AFN,27,0.42
ZWE,2026-05-15,Midlands,Gokwe South Urban,Gokwe,5425,-18.22,28.95,oil and fats,Oil (vegetable),96,L,actual,Retail,USD,2.74,2.74
```

## 建议

**结论：端点已变需改适配**——不是「可直接点亮」。三个理由：

1. **park 的根因（202 空体/不可直读）已不成立**：旧资源当前 302→S3 206，可正常流式读取。若只想回填历史，改回 `parked: false` 即可跑通。
2. **但旧库已停更 5 年**：内容止于 2021-08，点亮后只有静态历史，月频 cron 全部落空（且 `golden` 锚的 2014-01 值仍成立，会造成「健康但无新增」的假绿）。
3. **增量在 `global-wfp-food-prices`，schema 完全不同**：无 `adm0_name/mkt_name/cm_name/mp_*`，改为 `countryiso3/date/commodity/market/price/pricetype/currency/unit/usdprice`。现 `spider.py` 的列映射与 `_resolve_resource_url()`（只取第一个 CSV）都需要重写。

改适配要点（供后续立项）：

- 资源选择：40 个按年分片，**只取当年 + 上一年**（≈42 MB + 60 MB），勿拉 620 MB 全库；按 `resource.name` 中的年份正则匹配，不硬编码 resource id。
- 列映射：`countryiso3→country`、`date→month(YYYY-MM)`、`pricetype→Retail/Wholesale`、`usdprice` 可作为新增 USD 归一价（旧模型无）。
- `golden/001-wfp-food-price.json` 必须重写（旧 schema 值在新库里取不到同名列）。
- cron：每月一次（`data_update_frequency=30`），错开 HDX 的周更新高峰；单次约 100 MB 流量、流式解析、`limit` 断流。
- 若短期只想要「活着的历史源」，最小动作是把 manifest 的 `source_url` 与 spider 的资源选择改到新年份分片；保留旧库作为回填路径亦可，但两者不要同时调度。

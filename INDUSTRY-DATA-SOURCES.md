# 行业数据源侦察簿（持续更新）

> 目标：为指标注册目录 / fd-industry-data 适配器体系寻找**接口性质（稳定 HTTP 端点）且周期性更新**的行业数据源。
> 发起：2026-10-02，用户指令——**12 路子代理持续满编侦察**，本文档为唯一事实源，定期汇报。

## 网络环境与代理规则（用户指令，2026-10-02）
- **海外源打不通 ≠ 放弃**：公司有海外 proxy 节点，海外数据走代理反而好爬；国内 proxy 才稀缺。
- 本机代理：`http://127.0.0.1:7890`（HTTP/SOCKS 同端口；使用前先探测，端口可能变）。
- 执行方式：海外站点先直连试一次 → 失败即 `curl -m 25 -x http://127.0.0.1:7890 -sL ...` 复测；代理通了照样 ★接，标注「需走代理」。国内站点禁走代理、直连为准。结论写明【直连=x / 代理=x】。
- 舰队既有海外代理：gost-own 10.1.0.4:30080（集群侧备用出口）。

## 评估维度
| 维度 | 说明 |
|---|---|
| 接口性质 | 稳定 HTTP API（JSON/CSV/SDMX/CKAN），非仅网页/PDF |
| 周期性 | 日/周/月/季/年，更新节奏与延迟明确 |
| 免费程度 | 免 key / 免费注册 key / 付费 |
| 历史深度 | 可回溯的时间跨度 |
| 行业价值 | 行业口径颗粒度、中国相关度 |
| 接入成本 | 适配器工作量 S/M/L + 反爬/条款/合规风险 |

## 硬性排除
- 用户已有且停爬：~~股票价格、上市公司财报~~（**2026-11-07 已反转，见下方决策记录**；仅余非证券类目）、金融行情（大宗现货/行业高频价=灰区，标注待裁决）
- 美国公司财务事实源（SEC EDGAR 等）与 GFW 类源维持排除（与证券业无关，不因 2026-11-07 反转而扩大）

### 决策记录：证券业停爬排除反转（2026-11-07）
- **日期**：2026-11-07
- **范围**：证券业线——A 股行情（日线 OHLCV）、上市公司财报与公告（三大报表/财务指标/业绩报表/主营构成）、市场结构数据（两融余额、北向资金、沪深市场统计、证券业协会经营数据）
- **理由**：用户拍板全量放行（openspec change `add-securities-industry-line`，proposal.md Why 节）：证券业作为行业线需要服务端现役供给，价格概念族（目录 id 233-238）按原 id 复活
- **不变项**：10-07 决议中对非证券业数据的排除（SEC EDGAR、GFW 类）维持不动；原条目仅标注取代、不删除
- **回退锚**：本记录+`MCP-REGISTRY.md` daas 数据面条目反转注记+`wire-analysis-presets` spec 修订三处同步回退即恢复原政策

### 决策记录：银行业财报局部重开（2026-11-07）

- **日期**：2026-11-07（决策）／2026-11-08（范围机器可读落地）
- **范围**：**42 家 A 股上市银行**（东财银行板块 BK0475 实时成分，2026-11-08 实测 42 家 = 33 沪 + 9 深）的**四类定期报告**（年度报告/半年度报告/第一季度报告/第三季度报告），近三年报告期，走 **cn-report 车道**（`fd-cn-report` ingest，openspec change `awaken-banking-report-ingest`）
- **理由**：银行业线核心诉求是「监控主流银行财务细分」。上游管道与规则侧已在册（26 条 bank-scoped LLM 规则 + 180 条申万银行 801780 script 规则），但 daas.db 的 report_documents/report_sections 长期 0 行——不是能力缺失，是 ingest 从未规模投产。故按「有规则、无数据」缺口唤醒，不新建机制
- **口径细则**：orgId 一律取巨潮官方映射表（`/new/data/szse_stock.json`），**不按交易所前缀拼接**——官方映射同一交易所混用 `jjxt`/`gssh`/`9900`/`gssz` 四种前缀（601398→`jjxt0000019`、600036→`gssh0600036`、002142→`9900003281` 均实测），交易所只能按代码段判定；`szse_stock.json` 覆盖全部 A 股 6263 行，可作唯一真源
- **排除项**：**纯 H 股银行维持二期**（15 家活跃，本期输出须明示排除、不得表述为已覆盖）；OCR 类源维持 2026-10-13 裁决（图片型报表暂不处理）
- **并列关系**：与「证券业停爬排除反转（2026-11-07）」「农业财报局部重开（2026-11-08）」**三条并列，各自范围互不覆盖**；本记录不修改、不取代任何证券业条目
- **扩大锚**：任何超出上述范围（H 股结构化财报、非上市银行、全 A 股财报重爬）须另立 change，不得以「同一管道顺手」口头豁免

### 决策记录：农业财报局部重开 + 港美事件面边界重述（2026-11-08）

- **日期**：2026-11-08
- **范围（重开）**：申万农林牧渔 A 股成分全量，四类定期报告（年报/半年报/一季报/三季报）近三年，走 cn-report 车道（openspec change `awaken-agriculture-report-ingest`）
- **范围（重述）**：港股（HKEX 披露易）与美股（SEC EDGAR）**仅事件面**——披露日期/公告类型/报告期/盈警类型/头条营收净利；**不做 XBRL 或其他结构化财务细分**
- **理由**：用户 2026-11-08 拍板农业线财务监控深度=「A 股深抽 + 海外事件面」；美股事件面是「何时披露了什么」，不构成完整财务数据面，与用户既有 A 股数据不重叠，属对上方 SEC 排除条的范围重述而非解除
- **不变项**：农资类（化肥/农药/种子生产/农机）上市公司不进入公司财务监控；商业聚合商现货报价维持排除；OCR 类源维持 2026-10-13 裁决（暂不处理）
- **并列关系**：与「证券业全量放行（2026-11-07）」「银行业局部重开（2026-11-07）」三条并列，各自范围互不覆盖
- **扩大锚**：任何超出上述范围（如美股 XBRL 细分、港股结构化财报）须另立 change，不得以「只是标题/只是补几个字段」口头豁免

- 已接入源（fd-industry-data/spiders，46 个）：agri-info, bls, caa, cap, chinamonitor, cisa, cisia, cnia, coinmarketcap, cqvip, cssn, dce, digitimes, eastmoney-data, eastmoney-futures, flower-*, fred-data, gtarsc, hqcdc, inmetals, intrinio, isee, kitco, metal-com, mof, mysteel, nbs_gdp, nbs-stats, nhc, people-daily, polygon, rmfyalk, stat-gov, toutiao-open, wanfangdata, wechat-mp, weibo-open, worldsteel, yn-agriculture, yunnan-flowers, zce
- 宏观体系已覆盖：国家统计局 NBS/cnstats/esData、世界银行、金十、年鉴

---

# Wave 1 结果汇总（2026-10-02 完成）

## ★接 候选总表（34 项，全部经实测）

| # | 源 | 方向 | 端点要点 | 鉴权 | 周期 | 直连/代理 |
|---|---|---|---|---|---|---|
| 1 | 商务部数据中心 | K | POST data.mofcom.gov.cn/datamofcom/front/totalmonth/query 免鉴权返全序列 JSON（货物进出口月度至 202608） | 无 | 月 | 直连✅ |
| 2 | 国家邮政局快递月报 | K | spb.gov.cn/common/search/{channelId}?_isJson=true + 静态正文（业务量/收入/CR8，连续 24 期无缺） | 无 | 月 | 直连✅ |
| 3 | 工信部 gxsj | K | miit.gov.cn/api-gateway/jpaas-publish-server/.../build/unit（软件业/通信业等 7 栏月度） | 无 | 月 | 直连✅ |
| 4 | 专资办电影票房 | B/D | zgdypw.cn/data/searchDayBoxOffice.json + zgdypf.zgdypw.cn/getDayData、getPeriodData（日/周/月全有，回溯 2024+，实时大盘盘中可取） | 无 | 日 | 直连✅ |
| 5 | 中央气象台 | B | nmc.cn/rest/weather?stationid=（实况逐时+7日预报；/rest/province 枚举站码） | 无 | 时 | 直连✅ |
| 6 | 水利部水雨情 | B | xxfb.mwr.cn/portal/hydroinfoByDays（日通报 JSON）+ surpassWarningInfo 超警 POST | 无 | 日 | 直连✅ |
| 7 | Eurostat | A | ec.europa.eu/eurostat/api/dissemination/.../sts_inpr_m（制造业生产指数 1953 起，T+35 天） | 无 | 月 | 直连✅ |
| 8 | UN Comtrade | A | comtradeapi.un.org/public/v1/preview 无 key 可用；主 API 免费订阅 key，月度 HS6 贸易流 1962 起 | 免费key | 月 | 直连✅ |
| 9 | IMF PCPS | A | api.imf.org/external/sdmx/2.1/data/...（初级商品月度价 1990 起；**旧 dataservices.imf.org 已死**） | 无 | 月 | 直连✅ |
| 10 | OECD SDMX | A | sdmx.oecd.org/public/rest/data/...（13 维 key 需按 DSD 拼；CLI/工业景气） | 无 | 月/季 | 直连✅ |
| 11 | DBnomics | C | api.db.nomics.world/v22（聚合 94 机构，白捡 SAFE 外管局+CEPII BACI 双边贸易） | 无 | 随上游 | 直连✅ |
| 12 | ECB Data Portal | C | data-api.ecb.europa.eu/service/data/EXR...（CNY/EUR 日汇率+BSI/YC/SUP 独家口径） | 无 | 日/月 | 直连✅ |
| 13 | Open-Meteo 三件套 | C | api/archive-api/air-quality-api.open-meteo.com（免 key，archive 实测 1940 起，北京 PM2.5 小时值） | 无 | 时 | 直连✅ |
| 14 | 搜猪网生猪大数据 | D | soozhu.com/price/data/center/（生猪/仔猪/玉米/豆粕 8 序列日更，AKShare 同源佐证）〔价格类待裁决〕 | 无 | 日 | 直连✅ |
| 15 | 高德开放平台 | D | restapi.amap.com/v3/traffic/status/*（2 分钟级交通态势，免费 key 2000 次/日） | 免费key | 2min | 直连✅ |
| 16 | 生意社 100ppi | D | 100ppi.com/cindex/（300+ 大宗现货价+BCI/BPI，华为云 WAF 两步固定 cookie 可过）〔价格类待裁决〕 | 无 | 日 | 直连✅ |
| 17 | 深圳开放平台 | E | opendata.sz.gov.cn/api/{接口ID}/{版本}/service.xhtml?appKey=（~2986 个数据接口，区县月度社零/统计月报） | 免费appKey | 月 | 直连✅ |
| 18 | data.gov.uk | E | CKAN /api/3/action/package_search|package_show（免鉴权；CKAN 通用适配器基准） | 无 | 随机构 | 直连✅ |
| 19 | data.gov 目录 | E | api.gsa.gov/technology/datagov/v4（DEMO_KEY 即用；只做发现层） | 免费key | - | 直连✅ |
| 20 | OpenAlex | F | api.openalex.org/works 按月 filter 计数=研发活跃度月度序列（1800s 起，日更；S3 全量快照可离线） | 无 | 日 | 直连✅ |
| 21 | GLEIF | F | api.gleif.org/api/v1/lei-records（每日黄金副本；initialRegistrationDate 过滤→全球新设法人月度序列） | 无 | 日 | 直连✅ |
| 22 | 国标检索 std.samr | F | std.samr.gov.cn/gb/search/gbQueryPage 纯 JSON（发布/实施/废止=监管强度序列；行业标准/团标同构可扩） | 无 | 实时 | 直连✅ |
| 23 | ENTSO-E | G | transparency.entsoe.eu/api（EU27 15min/1h 发电/负荷/跨境，2015 起；免费 token 注册+邮件申请） | 免费token | 15min | 直连✅ |
| 24 | EIA v2 | G | api.eia.gov/v2/electricity/rto/*（美国小时级电网+国际月度 215 国；免费 key 秒发，首连建议重试） | 免费key | 时/月 | 直连✅ |
| 25 | Ember | G | api.ember-energy.org/v1/{dataset}/{monthly,yearly}（215 国电力结构/排放/装机，月更，OpenAPI 全公开） | 免费key | 月 | 直连✅ |
| 26 | USDA QuickStats | H | quickstats.nass.usda.gov/api/api_GET（美国农情周/月报级，州/县级，1900s 起） | 免费key | 周/月 | 直连✅ |
| 27 | USDA PSD | H | api.fas.usda.gov/api/psd/*（全球农产品供需平衡表月度，1960 起） | 免费key | 月 | 直连✅ |
| 28 | FAOSTAT Bulk | H | bulks-faostat.fao.org/production/*.zip（API 已强制 401，走 bulk ZIP 规范化 CSV，1961 起） | 无 | 年 | 直连✅ |
| 29 | IMF PortWatch | I | services9.arcgis.com/.../Daily_Ports_Data/FeatureServer/0/query（2065 港+28 咽喉日度 portcalls/吨量，2019 起）＋Chokepoints 同实例 | 无 | 日 | 直连✅ |
| 30 | NASA FIRMS | I | firms.modaps.eosdis.nasa.gov/data/active_fire/.../Global_24h.csv（全球 24h 火点免 key；MAP_KEY 可自定义 bbox） | 无(可选key) | 日 | 直连✅ |
| 31 | OpenSky | I | opensky-network.org/api/states/all?bbox（匿名实时全球航班；历史需账号，自建采样） | 无 | 10s | 直连✅ |
| 32 | NASA POWER | J | power.larc.nasa.gov/api/temporal/{hourly,daily,climatology}/point（免 key，辐照/气象 1981/1984 起） | 无 | 时/日 | 直连✅ |
| 33 | USGS NWIS | J | waterservices.usgs.gov/nwis/{dv,iv}（美国水文 15-60min/日值，部分站 100+ 年） | 无 | 时/日 | 直连✅ |
| 34 | NOAA NCEI | J | ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries（全球 10 万站日值，GHCN 1763 起） | 无 | 日 | 直连✅ |
| 35 | Treasury FiscalData | L | api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/...（免 key，日频国库+月度汇率） | 无 | 日 | 直连✅ |
| 36 | USAspending | L | api.usaspending.gov/api/v2/（联邦合同按 NAICS 月度聚合=行业需求信号，FY2001 起） | 无 | 日(可聚合) | 直连✅ |
| 37 | Census API | L | api.census.gov/data/timeseries/eits/{mots,wts}+CBP（分行业月度零售批发/企业结构；**免费 key 必须**，防 HTML 错误页伪装 200） | 免费key | 月 | 直连✅ |
| 38 | EU TED | M | POST api.ted.europa.eu/v3/notices/search（欧盟招标/中标含金额+CPV 行业码，日更；另有 eForms 批量 XML 补史） | 无(可领key) | 日 | 直连✅(匿名限速) |
| 39 | 世行采购公告 | M | search.worldbank.org/api/v2/procnotices（42 万条，公告量口径，无金额字段） | 无 | 日 | 直连✅ |
| 40 | Kaggle Datasets | N | kaggle.com/api/v1/datasets/list|download（实测免 key 全链路含 ZIP 下载） | 无(建议注册) | 随数据集 | 直连✅ |
| 41 | HuggingFace(镜像) | N | hf-mirror.com/api/datasets（主站直连超时，镜像全兼容 200；实测 15min 刷新的周期数据集） | 无 | 随数据集 | 镜像✅ |
| 42 | OpenDataSoft | N | data.opendatasoft.com/api/explore/v2.1/catalog（10.2 万数据集聚合目录，免 key；**publica 旧域名已死，必须 v2.1**） | 无 | 随源 | 直连✅ |

## 各路要点与放弃/待复核清单

### A 国际官方统计
- 备选：BIS stats（偏金融宏观）、ILOSTAT SDMX（服务端 SQL bug，须显式拼 5 维键）、UNIDO stat（Accept 头怪癖，POST 驱动，内容独特）
- 放弃：ITU DataHub（Akamai 403）→ **Wave2 代理复测**；UNdata（遗留接口）
- 坑：IMF 旧端点 dataservices.imf.org 已死（若有旧适配器引用需迁 api.imf.org）；Eurostat 时间参数须 `2024-06` 格式

### B 中国官方高频
- 备选：农业农村部 pfsc.agri.cn（今日报价+市场名录公开，日指数需登录，只能自今日起累积）、环交所碳价（gateway 401，可解析 shtml）、空气总站（POST 被重置）、data.cma.cn（需注册）
- 放弃：海关 stats.customs.gov.cn（412 瑞数墙）、中电联/能源局/民航局/港口协会（PDF 为主）
- 坑：endata.com.cn 已易主艺恩，专资办数据整体迁 zgdypw.cn

### C 全球聚合器
- 备选：OWID（country 过滤参数失效需本地过滤）、HDX（非结构化 CKAN）、WB Data360（WDI 与已有世行重复，增量库可用；官方 data360-mcp 可直挂公司 MCP）
- 放弃：datahub.io（平台陈旧）
- 发现：SAFE 外管局经 DBnomics 可取；BACI HS 双边贸易 2800 万条序列

### D 中文商业平台
- 备选：上海航运交易所（端点参数已定位 `/index/mutipleIndex`，需登录 session+CSRF；**版权声明商用需授权·待裁决**）、乘联会镜像 cada.cn（月度 HTML）、中物联 LPI（200 可达未深测）
- 放弃：猫眼（signKey 签名墙）、百度指数（风控 10018）、爱企查/企查查（免费层无趋势）、招聘平台（登录+验签）、今日酒价（仅小程序）、硅业分会（DNS 不通）
- 模板：华为云 WAF 两步固定 cookie 法可复用

### E 政府开放平台
- 备选：北京（appkey 逐集审批）、浙江（16,871 API 质量参差，待筛经济主题）、山东/贵州；上海（瑞数 412→自动化放弃）
- 坑：data.gov 已弃 CKAN；加拿大 CKAN 伪 200 WAF（CKAN 适配器要响应体嗅探）；Socrata 全域中国 403 → **Wave2 代理复测**

### F 专利论文实体
- 备选：Crossref（与 OpenAlex 重叠）、Europe PMC（医药切片）、data.uspto.gov（PatentsView 迁移中，待注册 key）、EPO OPS（可达，10.6s 延迟+4GB/周）
- 放弃：Semantic Scholar（429）、OpenCorporates（401）、PATENTSCOPE（SOAP+协议）、CNIPA（无 API）
- **待裁决：SEC EDGAR（可达 200，财报邻域）**

### G 能源电力
- 备选：GIE AGSI/ALSI（欧洲储气/LNG 日频，免费 key 一把通两平台）、Eurostat 能源域（维度码表复杂）、ElectricityMaps（碳强度）、AEMO NEMWEB（CF 间歇拦 → **代理复测**）
- 放弃→**Wave2 代理复测：Elexon BMRS（Azure WAF 403，免 key 文档全开，翻案价值高）**
- 放弃（维持）：IRENA（无 API）、广州/北京电力交易中心（仅市场主体可申请）

### H 农业食品渔业
- 备选（价格类·待裁决）：FAO 食品价格指数 CSV（1990 起月度，官方固定链接）、WFP 市场粮价（HDX 托管，90+ 国市场级月度）、GFW 渔业 API（可达，**条款仅限非商业·需法务**）
- 放弃：USDA AMS MARS（OAuth 门禁）、GIEWS FPMA（无公开接口，WFP 路线覆盖）
- 发现：AMIS 市场库（SPA 无 API）；Eurostat 农业价格指数 API 可用

### I 交通卫星
- 备选：adsb.lol（大陆覆盖稀疏）、AISStream（需常驻 websocket 自建历史）、Copernicus Data Space（影像级 L）、VIIRS 夜光 VNL（月度，免费账号）
- 放弃：airplanes.live（CF）→ **代理复测**；OSM Overpass（406/镜像超时）→ **代理复测**；AISHub（会员邀请制）
- 发现：PortWatch 咽喉要道同实例免费拿；OurAirports 全球机场主数据 CSV

### J 全球环境气候
- 备选：OpenAQ v3（401 免 key，全球聚合但中国站点稀疏）、EPA AirNow（401，仅美国）、NOAA SWPC（Kp 指数 1min/3h，行业面窄成本 S）、NDBC 浮标（10min 海洋）、ERA5/CAMS（CDS/ADS 免费账号但队列+L 成本）
- 发现：EPA AQS（合规级历史）；OpenAQ 有社区 MCP server

### K 中国部委
- 备选：央行社融/货币统计（静态页直链 xlsx 已验证，**金融邻域待裁决**；附件 URL 规律可预测）、市场监管总局（SPA，季度新闻稿）
- 放弃：税务（被 mof 覆盖）、人社（SPA+重复）、住建（月度口径在统计局）、文旅/国资/林草/烟草（低频/不可达）
- 发现：商务部同族端点（服务贸易/外资/ODI）可逐个调参扩展；邮政局快递发展指数独立栏目

### L 美国官方经济
- 备选：BEA API（分行业 GDP 唯一官方源，仅差注册一步）、HUD（403 需 token）、Dallas Fed WEI（周度 XLSX）
- 放弃：EPA ECHO（服务路径全 404 疑迁移）、Philly Fed/SBA（未 API 化）
- 坑：Census 无 key 返回 HTTP 200 的 HTML 页——适配器必须校验首字符

### M 招投标
- ★TED + 世行 procnotices；备选：data.ggzy 官方「接口服务」机构申请（唯一合规路径）、国铁 cg.95306.cn、国网 ecp（HTML M 级）
- 放弃：ccgp（IP 级限流墙）、cebpubservice（验证码）、军队采购（未连通+敏感）、亚开行（不可达）
- 发现：TED eForms 批量 XML 适合历史回填；《招标公告和公示数据接口规范》(10号令)是官方对接规范

### N 数据集托管
- 备选：data.world（401 需免费 key）、OpenML（静态 ML 基准，不符口径）
- 放弃：Zenodo（403 风控）→ **代理复测**；figshare（403）→ **代理复测**；Academic Torrents（超时+BT 不适配）、Papers with Code（已关停）
- 发现：Kaggle 免 key 全链路属未承诺行为，可能加限；Huwise/ODS 单门户 API 同构可一适配器复用

---

# Wave 2（2026-10-02 派出，12 路满编）

| 路 | 任务 | 状态 |
|---|---|---|
| W2-1 | 产业垂直：半导体电子（Census M3/TWSE/KOSIS） | ✅ |
| W2-2 | 产业垂直：医药健康（openFDA/ClinicalTrials v2/中检院批签发） | ✅ |
| W2-3 | 产业垂直：汽车新能源（IEA EV/OpenChargeMap/AFDC） | ✅ |
| W2-4 | 产业垂直：旅游文娱体育（Steam/BOM/football-data） | ✅ |
| W2-5 | 产业垂直：海外房地产建筑（UK HPI/StatCan/ABS） | ✅ |
| W2-6 | 产业垂直：矿业化工材料（Eurostat C20 实锤，其余偏薄） | ✅ |
| W2-7 | 深潜：中国官方高频端到端（6/6 打穿） | ✅ |
| W2-8 | 深潜：国际宏观端到端（6/6 打穿，IMF/OECD key 结构修正） | ✅ |
| W2-9 | 深潜：能源气候（7 源验证+key 流程盘点） | ✅ |
| W2-10 | 深潜：交通卫星（PortWatch 分页策略+Elexon/AEMO 翻案） | ✅ |
| W2-11 | 深潜：美国官方+农业（USAspending 跑通+Census 端点修正） | ✅ |
| W2-12 | **代理复测翻案组**（6 翻案 / 1 备选 / 5 维持死） | ✅ |

## Wave 2 结果（2026-10-02 完成）

### 新增 ★接（15 个）
| 源 | 垂直 | 要点 |
|---|---|---|
| Census M3 | 半导体 | NAICS 334413 出货/库存/订单月度，1992 起；免费 key（全 census 查询强制 key） |
| TWSE OpenAPI 月营收 | 半导体 | openapi.twse.com.tw/v1/opendata/t187ap05_L，全台上市当月营收 JSON 无 key，產業別可滤半导体；历史靠正向累积 |
| KOSIS OpenAPI | 半导体 | 韩国生产指数/出口月度，免费 key，直连通 |
| openFDA | 医药 | 不良事件月度 10 万+记录（2004 起），免 key（240/min），审批/器械同构端点 |
| ClinicalTrials.gov v2 | 医药 | `countTotal + AREA[StudyFirstPostDate]RANGE` 一次返回整月注册量（2024-01=3776），2000 起，免 key |
| 中检院批签发 | 医药 | `POST bio.nifdc.org.cn/pqf/search.do?formAction=list1` 疫苗/血制品月度批签发 13 字段结构化，免 key 无验证码（https 自签证书需 -k）——国内黄金源
  - **2026-10-02 落地修正**：list1 按品名检索已在服务端清空（任意查询返 0 条）；在用入口=每周公示汇总 `search.do?formAction=pqfGs`→`listGsxq` 周页，**8 字段口径**；站点整站 301 至 **bio.nidc.org.cn**（院更名） |
| IEA Global EV Data | 汽车 | `api.iea.org/evs/` 无 key，全球 EV 销量/保有量/渗透率 2010-2025 + 情景投影 |
| OpenChargeMap | 汽车 | 全球充电桩点位，免费 key |
| Steam Web API | 文娱 | CCU 在线人数+评论聚合，免 key【store 域直连✓ / api 域需代理】 |
| Box Office Mojo | 文娱 | 海外票房 HTML 年/周页 1977 起，直连，低频抓取 |
| football-data.org | 体育 | 12 顶级联赛免费 tier，10 req/min |
| UK HPI | 房地产 | `publicdata.landregistry.gov.uk/.../UK-HPI-full-file-YYYY-MM.csv` 官方指数 1995 起月度，无 key，支持 Range |
| StatCan bulk CSV | 房地产/建筑 | `/n1/tbl/csv/{productId}-eng.zip`：NHPI 1981 起+建筑许可，无 key（WDS REST 是坏的，走 CSV） |
| ABS SDMX | 建筑 | `data.api.abs.gov.au/rest/data/BA_GCCSA/all?format=csv` 澳洲建筑许可月度，无 key（注意 RPPI 2021Q4 已停更） |
| Eurostat C20 化工 | 化工 | 复用 sts_inpr_m（nace_r2=C20），月度生产指数；Prodcom 走 /api/comext/ 另一通道 |

### 代理翻案 ★接（6 个）
- **Socrata 系**（data.ny.gov / data.cityofchicago.org）：直连 403 → 代理 200 真 JSON → ★接【需代理】
- **figshare**：403 → 代理 200 → ★接【需代理】
- **HuggingFace 主站**：直连超时 → 代理 1.7s → ★接【需代理；hf-mirror.com 直连兜底】
- **AEMO NEMWEB**：直连 200（CF 拦截已消失）→ ★接【无需代理】
- **UNIDO SDMX**：Accept 换 `application/vnd.sdmx.data+json;version=2.0.0` + ISO 数字国码（156=中国）→ 直连 200 → ★接【无需代理，纯头部协商】
- **加拿大 CKAN**：裸 UA 被 F5 伪 200；完整 Chrome UA 直连即真 JSON → ★接【必须完整浏览器 UA】
- **Elexon BMRS**（W2-10）：代理下 `/bmrs/api/v1/system/frequency` 返回 50.044Hz 实时 → ★接【需代理】

### Wave C 代理组落地终态（2026-10-08）
- **socrata-ny**：data.ny.gov `k7gz-mn77` 交通燃料现货价（周频，NY 汽油/柴油 + WTI/Brent 四价列，2011-01 起）→ 单元 `spiders/socrata-ny/`，**已点亮首爬 100 行 success**。选集注意：Socrata 目录 API 是**联邦检索**（不指定 domains 会跨站返回同列表）；`$limit/$order` 必须 urlencode；数值列字符串需转 float。
- **socrata-chicago**：data.cityofchicago.org `bynn-gwxy` CTA 公交月度客流（2001-01 起，服务端 SoQL 聚合 `$group=month_beginning + sum(monthtotal)` 得全网月度乘次）→ 单元 `spiders/socrata-chicago/`，**已点亮首爬 100 行 success**。聚合别名 `sum_monthtotal` 是上游自动命名。
- **elexon-bmrs**：`datasets/TEMP` 日度有效温度（英国电网需求预测天气锚，31 天滚动窗）→ 单元 `spiders/elexon-bmrs/`，**已点亮首爬 31 行 success**。放弃端点证据：FUELINST 日期过滤被忽略恒返当天快照；B1610 参数齐全仍恒空；system/frequency 是实时流。
- **figshare 判死**（3 轮证据）：月发布量 ~10 万级（1000 条样本全落 1 小时）远超采样上限；无聚合端点（/v2/articles/stats 400、institutions/groups 404）；search 端点 `published_date_gte/lte` 与 Lucene 区间语法**均被静默忽略**（2025 区间返回 2026 条目）。转遗留，除非上游提供聚合能力再入批。
- 通道：PR #50/#51/#52 直建（fx01 出口，egress_secret 机制）→ 三闸全绿（96 manifests/94 units）→ 点亮 09d9eed（05:03/05:09/06:33 日跑）→ 首爬 3/3 success。建造通道注：子代理被 LLM 账户限流打死（11.5h 重试钟），改主会话直建。

### 深潜关键发现（W2-7~11）
- **mofcom 全家桶**：货物进出口（当年月度 19 字段）、服务贸易历年（1982→2025，44 行）、**利用外资月度 1983-12→2026-08 共 247 行（全站最深序列）**、ODI 碎片化；坑：仅 pageNumber 生效、必须带 Referer、返回裸双元素数组
- **专资办票房**：日榜可回溯 **2017-01-01**（10 年日粒度）；周榜 date 必须周一+withSvcFee=1；204 空响应与 `"<0.1"` 字符串需容错；两端口径差 0.7%
- **邮政局**：运行情况月度 36 期连续（2023-11→2026-09）；CR8/区域占比正文可正则；快递发展指数 GUID=`49357e62dbcc4693aa91b3685619cb88`（运行情况=`ce2d4d5628314ff7a81553529fb7f6a0`）
- **工信部**：pageId 已固化——软件业 `50bf589f36614b7394522245a13fedae`、通信业 `1434685f08314ae8ae78f78b6a5a7915`；裸 curl 403 必须 UA+Referer
- **中央气象台**：34 省 2529 站，站码为内部短码；`9999`=缺测占位
- **水利部**：仅最新一期（days 参数无效）；**汛期停刊**（每年 10/1~次年 5/31 空窗）
- **IMF PCPS 修正**：真实 key=`G001.PCOIL.INDEX.M`（4 段，World=G001 非 W00；商品码 PCOIL 非 PCPWOIL），416 obs 1992-01→2026-08；**只返 XML**（format 参数被忽略）；错 key 返回空数据集而非报错
- **OECD CLI 修正**：dataflow `OECD.SDD.STES:DSD_STES@DF_CLI`，中国 key=`CHN.M.LI.IX._Z.NOR.IX._Z.H` 140 obs；CSV 导出用 `format=csvfilewithlabels`
- **DBnomics 降级警示**：SAFE 镜像冻结在 2020-12（12 obs），不能当持续源；BACI_HS17=1781 万系列可用
- **UN Comtrade 降级警示**：preview 层中国月度止于 2024-12（美国正常）；单次上限 500 条；主 API 需免费 key
- **ECB BSI**：欧元区 M3 1980-01 起 560 obs，format=csvdata 最顺滑
- **ENTSO-E**：token 流程=注册+发邮件 transparency@entsoe.eu（主题 "RESTful API access"）3 个工作日；base=`web-api.tp.entsoe.eu/api`；无 token=401+code999 XML
- **EIA v2**：限流 <9000/h 且 <5/s；单次 5000 行；数值全字符串
- **GIE AGSI/ALSI**：key 永不过期；**错误也返 HTTP 200（查 error 字段）**；分页 ≤300；60 次/分
- **PortWatch**：滞后约 7 天，~6880 行/天；分页 1000/页 orderBy=portid（按 date 排序会超时）；chokepoints 同实例 42 点
  - **2026-10-02 落地修正**：上游已重建库——ports 现为 **2065 行/天**（2065×2825 天矩形完整），chokepoints **28 点**（非 42）；「~6880 行/天」为过时侦察数字
- **FIRMS**：中国 bbox 日均 ~2000 火点；MAP_KEY 邮箱即得（5000 次/10min）；area API 免全量下载
- **USAspending 修正**：正确端点=`search/spending_by_category`（**无尾斜杠**）+`search/spending_over_time/`（group=month 已跑通 FY2025 12 个月）；行业拆分=按月循环 12 次+客户端 2 位码汇总
- **Census 修正**：`mots/wts` 端点不存在→实为 `eits/mrts`(零售)/`eits/mwts`(批发)；无 key 500 查询/天；www 域有 Cloudflare，api 域干净
- **USDA**：QuickStats 全端点强制 key（邮箱即发）；PSD 实际用 API.Data.Gov key + `X-Api-Key` 头；BEA 36 字符 UserID、100 req/min
- **Open-Meteo/NASA POWER/USGS**：1950 上海 365 天满量、1984 乌鲁木齐 366 天满量、USGS 10 年日值无缺测——长回溯可行

### 维持放弃（代理也救不了）
ITU DataHub（AWS WAF JS 质询）、OSM Overpass interpreter（服务端 406 疑似全局故障，status 页正常）、Zenodo（出口 IP 风控 403）、airplanes.live（CF 质询）、FAO 旧镜像 fenixservices（源站 521 宕机；FAOSTAT 走 bulks-faostat 批量 CSV）

### W2 降级
- OpenSky → 备选：API/配额正常，但中国大陆 feeder 极稀（长三角实测 1 架/次），不能做中国空域指标
- VIIRS 夜光 VNL → 备选：免费账号仅人工下载，程序化批量官方要求付费订阅
- Semantic Scholar → 备选：代理可达但共享出口 429 频繁，需低频+退避+免费 key

# Wave 3 结果（2026-10-02 完成，12 路）

## 新增 ★接（~26 项）
| 源 | 方向 | 要点 |
|---|---|---|
| 中物联 chinawuliu | 物流 | `/xsyj/tjsj/` 栏目一个 spider 吃 5 条口径：公路运价周指数（周五发，meta description 机器可读）、LPI 月度、电商物流指数、社会物流总额；2015 起回溯 |
| 中钢协数据门户 chinaisa.org.cn | 钢铁 | **并入已占 cisa spider 扩展**：`POST /gxportal/xfpt/portal/getColumnList` JSON 免鉴权，粗钢旬报产量/库存（黄金口径，worldsteel 不覆盖中国旬度）+周度八品种价格指数；注意原 cisa spider 只指向 cisa.org.cn 兄弟站 |
| NBS 流通领域生产资料价格 | 大宗 | 旬度 HTML 内联表格 ~50 品（黑金/有色/化工/能源/农林/建材），2014 起回溯；**确认 nbs-stats spider 未覆盖→挂现有 NBS 通道增量，不新建源** |
| 四川统计局 | 区域 | 月度 38 行规整 HTML 表（规上工业+产品产量+固投+社零+税电指数），每月 16-18 日，requests 可解析 |
| 广东统计局 | 区域 | 月度 31 行表，唯一含 GDP+进出口总额的省级月度表；部分指标仅增速无绝对值需容错 |
| Carbon Monitor | 碳 | `datas.carbonmonitor.org/API/downloadFullDataset.php` 免鉴权全量日频 CSV（64.8 万行，38 国×6 部门，2019 起，滞后 2 月）；**必须 --compressed -m 300；旧 db. 域名勿用**；电力分燃料同款端点滞后≈0 |
| EDGAR v2026 | 碳 | `jeodpp.jrc.ec.europa.eu` 直链 ZIP 无鉴权：1970-2025 年度+月度×IPCC 行业+0.1° 网格 |
| GDACS（RSS+API） | 灾害 | 免 key 直连，GeoJSON 含 alertlevel，fromDate/toDate 回溯 2020+ |
| 应急管理部 mem.gov.cn | 灾害 | `/gk/tjsj/` 月度灾情通报（受灾人次/直接经济损失亿元），月中发布；**必须 --compressed** |
| FAO EMPRES-i BigQuery API | 疫情 | `api.data.apps.fao.org/api/v2/bigquery?sql_url=<公开.sql>` 免 key 直连 CSV：全球动物疫病事件（WOAH 镜像，2025 起 4.2 万行实测）；**FAO 通用 SQL 代理可复用到其他 FAO 数据集** |
| WTO ePing | 贸易壁垒 | `eping.wto.org/api/v1/notifications/getLatestNotifications` 匿名可用（当日新鲜）；HS+日期检索需免费注册；1995 起 |
| JODI-Oil | 能源 | `jodidata.org/_resources/files/downloads/oil-data/annual-csv/primary/{year}.csv` 确定性 URL，2002-2026 月度行 ~100 国，含质量旗 |
| JODI-Gas | 能源 | jodidb.org TableViewer 导出（aspx postback 略糙），2009 起 ~30 经济体 |
| 日本 e-Stat | 日韩零售 | `api.e-stat.go.jp/rest/3.0/app/json/...` 直连通，免费 appId：百货超市销售月度+三产指数+特定服务业 |
| KOSIS 零售/线上购物表 | 日韩零售 | 补齐表 ID：零售 `DT_1K41003/41012`（2020.01 起）、线上购物 `DT_1KE10041/10071`（2017.01 起品类细分） |
| Eurostat ei_bsco_m | 景气 | 消费者信心正确代码（`ei_bsci` 已 404）；1985 起月度 |
| 浙江开放平台 | 地方 | `POST /dopServer/dataCatalog/apiQueryPage` 目录/元数据免登录可编程，「统计月报」7 条经济类接口已定位 sourceCode；取数需 appKey |
| data.europa.eu SPARQL | 发现层 | `bif:contains "'econom*'"` 语法秒回，2,918 经济数据集可按 dsModifyDate 增量 |
| Eurostat comext | 中欧贸易 | **SDMX 2.1 端到端打通**（dataflow DS-045409→DSD 6 维→data）：EU-CHN 月度 HS6 贸易实数（德自中锂电 2025-07=€8.15 亿）；product 须 6 位 HS、reporter 不收聚合码 1Z |
| OurAirports | 维表 | airports.csv 12.7MB 19 字段，航空类主数据 |
| AMIS | 粮农 | `POST amis-9189b.appspot.com/fetch {"query":"<SQL>"}` 无鉴权直查 BigQuery（G20 八商品供需）；**appspot 被墙必须走代理** |
| NOAA SWPC | 空间天气 | Kp 指数 3h/10.7cm 通量，秒回免 key，成本极低 |
| AFDC | 美国能源 | 页面→正则提 `/files/u/...xlsx` 直链→下载，全链路无鉴权（S 级自动化模板） |
| World Bank data360-mcp | MCP | `pip install data360-mcp==0.1.3` 6 工具无 key，MIT，接公司 open-data MCP 仅加一条配置 |
| Eurostat apri_pi_outq | 农业价格 | ID 修正（`apri_pi05_outq` 已失效），季度农业产出价格指数 |

## 备选
ReliefWeb（v2 需预批准 appname，建议提申请）、EM-DAT（注册年度下载）、CEADs（人工注册下载，口径最佳）、Global Carbon Budget、Climate Watch（滞后 2-3 年）、cpcifdata（koala token，需浏览器取数）、mei.net.cn 机械联合会（纯文字稿）、畜牧业协会禽/牛子站、橡胶协会（图片需 OCR）、GEM 设施主数据（Sheets 需代理）、IEA Highlights（年度节选）、EPA AQS（key 即发）、NDBC 浮标、MTA 公交小时客流（代理）、Google Trends（429 强反爬，仅 RSS 热词可用）、教育部公报（年度网页）、OpenAIRE Graph（旧 API 2026-05-31 停用警告）、CCTD（本网络 TCP RST）

## 死胡同（新）
发改委价格监测中心（内部系统）、满帮/G7（无公开 API）、Baltic Exchange（会员制）、OPEC（WAF+注册）、Argus/Platts（付费）、Copernicus EMS（无 REST）、Swiss Re/Munich Re（无 API/会员）、DesInventar（失联）、CHEAA/产业在线/中纺联/酒业/乳品/肉类/CCFA/造纸协会（无公开结构化数据）、WAHIS（SPA 400+CF 拦，用 EMPRES-i 替代）、海关检疫警示（412 复确认）、USDA GAIN（双路 403）、中国碳市场公告（网页公告型）

## 经验教训（接入手册素材）
- **dataset ID 不可直接采信**：Eurostat `ei_bsci`→`ei_bsco_m`、`apri_pi05_outq`→`apri_pi_outq` 两例失效；接源前必须复测现行代码
- spider 命名撞车：`spiders/caa` = 中国自动化学会（非畜牧业协会）；`cisa` spider 指向 cisa.org.cn 而 chinaisa.org.cn 才有数据门户——扩展时别混淆
- 带 `[]` 的 API URL 必须 `curl -g`；MEM/Carbon Monitor 必须 `--compressed`；国内协会站（CCTD/煤协/数字水泥）对数据中心 IP 段 TCP RST
- AMIS/FAO 的 BigQuery SQL 代理模式（免 key、POST {"query": SQL}）值得作为一类接入范式记录


## Wave 日志
- 2026-10-02 Wave 1：首派 6 路；E/F 完成；A~D 被取消后随用户升级指令重启
- 2026-10-02 Wave 1'：12 路并行（A,B,C,D 重启 + G~N 新增）→ **全部完成**，34+ ★接 / 备选 ~20 / 放弃 ~25（其中 ~13 个列待代理复测）
- 2026-10-02 用户纠偏：海外源直连失败≠放弃，本机代理 127.0.0.1:7890 可用 → 已固化为「网络环境与代理规则」
- 2026-10-02 Wave 2：12 路派出（6 产业垂直补网 + 5 深潜验证 + 1 代理复测翻案）→ **全部完成**：新增 ★接 15、翻案 ★接 6、降级 3（OpenSky/VIIRS/SAFE 镜像）、维持放弃 5
- 2026-10-02 Wave 3：12 路派出（4 新垂直 + 2 协会深筛 + 能源补网 + 省级统计局 + 贸易壁垒 + 海外零售 + 2 遗留回收）→ **全部完成**：新增 ★接 ~26、备选 ~17、死胡同 ~15。发现密度开始下降（协会方向大半无公开数据），建议转入落地批次
- 2026-10-02 **落地批次 1（industry-source-expansion）**：本簿 ★接 源首次批量接入 fd-industry-data——11 个新单元（mofcom-data/spb-express/miit-gxsj/zgdypf-boxoffice/nifdc-batchcert/chinawuliu-logistics/sc-gd-stats/eurostat-api/dbnomics-api/portwatch-imf/carbon-monitor）+ 2 处既有扩展（cisa←chinaisa 门户、nbs-stats←流通领域价格）。全部真实取数验证（conformance gate 65 单元 0 违规），13/13 首爬成功（crawl_runs #721-734，累计 37,516 行），13 CronJob 已点亮（commit f527ef1，schedules 按侦察口径 日/周/旬/月）。落地修正：PortWatch 库重建（2065 行/天/28 咽喉）、中检院 list1 检索清空（改走每周公示 8 字段）、mofcom pageNumber 实被服务端忽略、chinawuliu 仅 http 可达。深历史（票房<2017、PortWatch 12 个月等）留 README 作后续可选任务；registry 语义登记按 unified-indicator-registry 另行推进
- 2026-10-07 **落地批次 2 · Wave A（industry-source-expansion-batch2）**：31 源全量接入 —— 生成单 31 张（b091402）→ 萬星门面 -32033 路由故障（agent 全命令拒收）→ **按 design D1 转人工直建兜底**（10 路并行子代理同日交付 PR #5-#35）→ 四岗独立复核 **31/31 全过零打回** → 合并预演零冲突 → 整波合并（PR 全归位、双远端同步，最终 main `df6d452`）→ **31 条错峰 cron 点亮**（分钟与既有零交集；ecb-exr=monthly 29 日档；wfp 上游冻结注记）→ **首爬 31/31 成功**（30 首过 + fao-empres 504 重试过；rows=100 为缺省截断，24-81 行者为回补口径）。实测纠偏 15 源：IMF key 4 段、OECD `/` 分隔+UA、openfda 方括号区间、clinicaltrials filter.advanced、pboc 现行栏目树+xlsx 月份法、FAO EMPRES 现行 SQL、fao-food-price 仅名义块、uk-hpi 路径改 house-price-index-data、statcan 368MB 取舍（仅 NHPI）、firms 13 列实相、worldbank fl 白名单、gleif 点号平铺、unido 真实数据面（actuator 取证）、gdacs 改 SEARCH 端点、openalex from/to 语法；golden 全部锚冻结历史值/结构常量。遗留：mwr-hydro 汛期空窗（2026-06 再入批）；wfp 上游 HDX 冻结 2021-08；既有 3 对同分钟 schedule（bls↔chinawuliu、carbon-monitor↔worldsteel、inmetals↔mofcom，小时错开不实际冲突）列入后续卫生项；Wave B（11 源 key 轨道，待专用邮箱开通）/ Wave C（eurostat 扩展 + 代理组）按 change 继续推进

## 决策记录（待用户裁决）

> **2026-10-07 状态更新（批次二拷问定案）**：1 已裁决=市场现货价维持排除、**FAO/WFP 官方粮价指数放行**（已接入）；2 已裁决=SEC 维持排除（与已有财报重叠）；3 已裁决=**央行社融放行**（已接入 pboc-monetary）；4 已裁决=GFW 维持排除（不开法务口子）；5 维持不开（付费通道无预算口）；6 落地中=专用公司域邮箱（data-sources@finddatatech.cloud，待管理员开通，Wave B 全部 key 注册前置）；7 已裁决=文娱**接 Steam+BOM**（BOM 已接入，Steam 列 Wave C）、football-data 不接
1. **价格类灰区**：生意社 100ppi、搜猪网、SCFI（含商用版权）、FAO 粮价、WFP 粮价、EU ETS 碳价——大宗/行业现货价是否放行？
2. **SEC EDGAR**：美国公司财务事实 API 可达（200），财报邻域是否豁免？
3. **央行社融/货币统计**：静态页 xlsx 极易接，金融邻域是否放行？
4. **GFW 渔业 API**：条款仅限非商业，是否用法务评估？
5. **付费替代**：100ppi 官方付费 API、上海航交所授权——是否有预算通道？
6. **Key 登记**：ENTSO-E/EIA/Ember/GIE/USDA×2/Census/Comtrade/高德/OpenChargeMap/KOSIS/M3 等免费 key 由谁统一注册管理？
7. **口径确认**：文娱消费类（Steam/BOM/football-data）是否纳入「行业数据」范围，还是仅作参考层？
- 2026-10-07 **落地批次 2 · Wave B keyed + Wave C 提前批**：门面 -32033 持续故障期以**人工直建兜底**全链交付 —— Wave B keyed 9 单元（eia-v2/ember/usda-quickstats/usda-psd/census-eits/census-m3/un-comtrade/jp-estat/openchargemap，8 项凭据实弹验证入集群密文 `fd-industry-source-keys`）+ Wave C 提前批 4（eurostat 四扩展/hf-datasets/amis-market/steam-ccu）。13 张 PR（#36-#48）复核 **13/13 全过零打回**，整波合并（main `8689692`），**9 条错峰 cron 点亮 + eurostat-ext 乘既有节拍**，首爬 **7/9 成功**（census×2 因 api.census.gov tencent 站 Errno 101 回熄待代理；fao-empres 504 重试过；hf/amis/steam 静默待 gost）。实测纠偏 10+：Ember 宽表实相、PSD 复数端点、Census 必填谓词+首字符校验+行内 url 剥 key、m3 码位 MTM、OCM alpha-2+地理半径锚、e-Stat 两步流、Comtrade 订阅头、AMIS 50000 截尾帽/修订行/跨项目表名。**新坑三则**：①本机代理出口 IP 38.76.150.185 被 Socrata 全域/figshare LB 边缘封禁（socrata×2/figshare 暂缓，换 gost 出口可解）；②LLM 账户限流 1302（9 并发打满，改串行喂）；③机器重启=后台子代理全灭（恢复 SOP：盘工作树、半成品续建）。**KOSIS 判定排除**（OneID 强制韩国本人名义手机/I-PIN，外国身份不可过）。ENTSO-E 申请信已发（10-07，~10-12 批复，token 后补建第 10 单元）。
- 2026-10-08 **落地批次 3（★接 存量扫尾 4 源，当日闭环）**：noaa-swpc（Kp 地磁指数日级统计，直连）/ ourairports（机场维表类型计数快照，流式解析 12.7MB）/ afdc（美国替代燃料加注站年度×燃料，**免 key JSON 通道 `afdc.energy.gov/data/{id}.json`**；`/data.json` 返 406、map 图 JSON 无载荷等坑留档）/ jodi-gas（**发现接口 `api.publisher.jodidata.org/web/files/gas`→SDMX zip**，94 经济体×14 能流 2009-01..2026-07；jodidb.org aspx 与下载页 Vue 均未走）。4 PR（#54-#57）主代理独立复核零打回→合并（三闸 100 manifests/98 units）→错峰点亮→首爬 3/3 即绿（ourairports 大文件跑慢另证）。**留痕 2 项**：浙江开放平台（目录通但取数需 appKey，代理出口 Errno 54——待 key 轨道）、data.europa.eu SPARQL（代理下超时——待复测）。change=industry-source-expansion-batch3（strict 过）。
- 2026-10-07 **落地批次 2 · Wave B/C 深夜补完**：①census-eits/census-m3 经 **mihomo-fx01 出口复活点亮**（首爬 14/16 行；根因=api.census.gov 从 tencent 站 Errno 101，fx01 出口 38.76.150.159 可达；链路=cronjob 模板 egressSecret 参数→envFrom `fd-industry-egress-fx01` secret→urllib 环境代理；曾踩 envFrom 同键覆盖丢 source-keys 的坑已修）；②hf-datasets/amis-market/steam-ccu 同出口点亮（首爬 1/100/12 行）；③Comtrade 全链拿下（Azure B2C 用户过码开户→订阅 key 实测中国 HS854142 出口）；④e-Stat 全链拿下（仮登録→本登録→appId 发行→实测 26,947 表）；⑤暂缓=AMIS 表名修正后 socrata×2/figshare/elexon-bmrs（本机代理出口 IP 被三家边缘封禁，待换出口重建——gost 10.1.0.4 已死，xinru/chengsi 均不可达）。**Wave B 9 源凭据全验入库**（含 e-Stat appId/Comtrade 订阅键/各站账号密码入本地保险箱）。Wave B 状态：9/11 源在产，kosis 排除、entsoe-e 待批（10-07 申请信已发）。
- 2026-10-15 **落地批次 2 · Wave B 收尾（entsoe-e，第 10 单元，当日闭环）**：ENTSO-E token 自助获取成功（**平台 2026-10-07 申请后约 10-14 批准**；本机经 Keycloak `keycloak.tp.entsoe.eu/realms/tp` 登录 → 页面路由 `myAccount/webApiAccess`（旧 `/myAccount/clientmanagement` 已 404）→ Generate Token → 网络拦截捕获明文 API 响应）。`entsoe-e` 直建（PR #61，94f8853）：A75 分燃料实际发电（默认，捷克 `10YCZ-CEPS-----N`）/ A65 总负荷，`securityToken` **查询参数**鉴权（实测请求头形式 401 code999，仅 query 可用）；**token 全链脱敏**（行内 url 与全部异常文本 REDACTED，落库泄漏检查 0 行）。点亮 `2 4 * * *`（全仓 60 天窗口零重叠实证，c00fd2b 双推）→ 首爬 **run 2119 success rows=100 in 4.5s**（crawl_items 抽样=捷克分燃料发电真值：B14 核电 3992MW / B12 夜间光伏 4.96MW）。**集群内直连 web-api.tp.entsoe.eu 实测 200——不需出口代理**。**Wave B 11 源终态齐备：10 建成全点亮（含 census×2 经 fx01）+ 1 排除（KOSIS 韩国实名）**；整批门达成 → change 可归档。**附修**：Wave C/批次三 5 个 golden 误用守卫不支持的 `matches` 规则（`validate_sample` 只认 `{field, equals}`，health gate 静默失效）——已修复 + conformance gate 新增 `golden-schema-invalid` 规则防复发（同 PR）。

## 普惠金融方向（2026-10-12 用户指令：农业/房地产业/金融业从业人数多但普通人金融服务不足，优先覆盖）

### 覆盖诊断（实弹盘点在产 104 单元 + 本簿）
- **房地产·中国境内为零**：仅三个海外源（uk-hpi / statcan-bulk NHPI / abs-sdmx 建筑许可）。
- **金融·只有总量**：pboc-monetary（社融流量存量 + M0/M1/M2），无任何普惠口径（小贷公司、住户贷款结构、地区社融）。
- **农业·国际齐全、国内缺**：FAO/USDA/WFP/AMIS/EMPRES-i 都在，缺国内官方价格序列（MOA 生猪周报此前未接）。
- nbs-stats 只覆盖 easyquery 宏观（GDP/CPI/PPI/工业/人口/就业）与流通领域生产资料价格，**不含 70 城房价**。

### 落地批次四（change `inclusive-finance-sources`，4 源当日闭环：静默合入 d1f3098 → 点亮 82366de → 首爬 4/4 success run 1881-1884）
- **`cninfo-operating`** 上市公司月度经营数据：**巨潮 `POST /new/hisAnnouncement/query` 检索 API**（免鉴权，参数 `pageNum/pageSize/tabName=fulltext/searchkey/seDate/isHLtitle`）发现公告 → **东财 `np-cnotice-stock.eastmoney.com/api/content/ann?art_code=` 取纯文本正文**（实测广汽产销快报 3286 字全文，含「产量 136,150 辆」）。**关键坑**：①cninfo 详情页 `bulletin_detail` **不含正文**（实测无"产销/万辆"字样），正文必须走东财；②cninfo 给 `announcementId`、东财要 `art_code`，用东财列表 API `np-anotice-stock.eastmoney.com/api/security/ann?stock_list=<secCode>` 桥接（翻页须按 seDate 起点前推，固定页数会在历史窗口失配）；③2026-09 单月量级：产销快报 18、销售简报 27、运营数据 13、发电量 6、经营简报 9；④港股/REITs 在东财列表 `total_hits=0`（约占 20%）留痕跳过；⑤按搜索词顺序取会让单类目吃光小 limit，须 round-robin 交织保三领域覆盖。**零 PDF 依赖**（PDF 库镜像未装，`pypdf` 兜底路径仅验证可行性未采用）。首爬 80 行。
- **`pboc-inclusive`** 央行普惠三件：**扁平目录 `diaochatongjisi/116219/116225/` 不按年份分**（对比 `116319` 按年份分目录）——小贷季报（实测「4863 家 / 贷款余额 7229 亿元」）、金融统计月报（住户贷款/人民币贷款 282.35 万亿）、地区社融 31 省区（正文仅「附件 xlsx」→ 已做二段取数走 stdlib zipfile/xml，单位从表头实读）。**坑**：裸 UA 敏感，走 curl_cffi/FetcherSession `impersonate=chrome`（仓内 4 单元先例）；千分位逗号须剥离；小贷报告是季报，目录只回溯 6 页 ≈120 条，约两年后 2025Q3 会移出窗口（README 已记维护口径）。首爬 100 行。
- **`nbs-housing`** 统计局房地产两件：70 城商品住宅销售价格（`sj/zxfb/` 列表页发现 → 文章页 **12 张表**，实测一行两城 `[北京,99.8,97.7,97.8,唐山,...]`）+ 全国房地产市场月度（开发投资 47979 亿/-19.9%、施工面积 560770 万㎡）。**坑**：城市名 HTML 含空格须规整；12 表 = 6 唯一表 × PC/移动副本，表3/表4 是面积段分桶与设计列不匹配**显式跳过并记日志**；1 月发布无累计列（6 格 vs 8 格）须按表头推导块宽，`ytd_avg` 记 None 不填 0；golden 只锚结构位不锚数值（取「最新发布」，锚数值下月必失效会把换月变假故障）；小 limit 下 70 城会吃光配额，须做公平配额轮转。首爬 100 行。
- **`moa-hog-price`** 农业农村部生猪与猪肉价格周报：`ztzl/szcpxx/scxxfb/` 列表（`<a class="content">` + `pubTime`，首页 6 条 / 共 4 页 `index_1..3.htm`）→ 正文两段不同监测口径（**500 个县集贸市场和采集点**：活猪 11.07/猪肉集贸 20.98；**200 个批发市场**：批发均价 15.92），逐行标注 `monitor_scope` 不混；口径与品种矛盾时跳过留痕。**坑**：涨跌措辞为中文文字（跌/涨/持平/略跌/略涨），解析带符号数值（持平=0.0，不可解析=None）；周区间跨月跨年须按发布年回推；正文不写年，年份从 meta/列表发布时间锚定。首爬 36 行。

### 留痕三项（本轮未打通，转后续轨道）
1. **NFRA 金融监管总局普惠金融统计**（理想口径：涉农贷款/小微贷款余额）——站点为 Angular SPA，多路径探测只拿到 3964 字节空壳，后端 JSON 端点四种模式（`/cn/static/data/DocInfo/SelectByDocId.json` 等）全 404。**待逆向**。
2. **PBOC 金融机构贷款投向统计报告**（历史普惠小微/涉农贷款经典来源）——现行 `116319` 目录下只有社融/货币统计概览/信贷收支/金融市场统计/CGPI 五类，无「贷款投向」栏目；站内搜索端点 404。**改版待重新定位**。
3. **住建部住房公积金统计**——`gongkai/fdzdgknr/sjfb/` 统计栏目以统计法规/调查制度为主（《住房公积金统计调查制度》等），实际数据序列（年度年报）未定位。**数据序列待定位**。

### 裁决合规说明
本批全部为**官方统计监测口径**（NBS/MOA/PBOC 发布），与 2026-10-07 放行的 FAO/WFP 官方粮价指数同类；**未触碰**维持排除的商业聚合商现货报价（生意社/搜猪网/SCFI）与财报邻域（SEC EDGAR）。央行金融统计扩展与已放行 pboc-monetary 同类别，无需重开裁决。

### 实弹验证的其他通道（未纳入本批，留档备用）
- **乘联会 cpcaauto.com**：裸 UA 返回「请使用浏览器访问本站」（33 字节），`curl_cffi impersonate='chrome'` 后周度/月度/指数三栏目全通（各 20 条）；月度分析正文含完整数值（9 月零售 161.8 万辆、同比 -28.0%、新能源渗透率 67.0%）。**待裁决**：属行业协会发布（非官方统计），口径需用户确认。
- **中汽协 caam.org.cn `/tjsj`**：栏目树可达（汽车产销 `cate_31`、零部件、进出口等），列表页 200 但标题需进一步适配。备用。
- 香港披露易 `hkexnews`、上交所公告 API `query.sse.com.cn`：均 200 可达，未做深探。
- 企业价格发布（万华化学挂牌价、宝钢月度价格政策）：站点可达但栏目结构未定，留后续。

### 排期审计方法论与修正（2026-10-13，change `socrata-cadence-alignment`）

**背景**：批次四点亮后我怀疑「全仓 10 组同分钟排期」是隐患，做了一轮完整审计，结论反转。

**审计口径（可复用）**：判定排期冲突 SHALL 用**分钟级真实并发模拟**，须同时计入三项——① 五维 cron 字段的实际交集（含 `*` 展开、逗号、范围、步长）；② 日期/星期的联合筛选（同分钟但不同日/星期不冲突）；③ **运行时长窗口**（源启动后占用若干分钟）。粗略口径「分钟字段相同即冲突」会产生假告警。

**结论 A（假告警，不需处理）**：10 组同分钟**全部无真实冲突**——靠小时/日期/星期维度错开。60 天逐分钟模拟（含实测时长）并发分布：**峰值 2 源**（2026-10-13 04:37 carbon-monitor + eastmoney-data），并发 ≥3 源 0 次。04 时窗「平均 8.6 源」是按最坏情况忽略日期/星期的统计假象，计入实际触发日后峰值仍为 2。单节点 4C/3G 无压力。

**实测运行时长基准**（`crawl_runs` 14 天，用于占用窗口估算）：`akshare` 均值 18.9 min / **峰值 106.6 min**（最长跑者，需重点避让）；`ourairports` 9.5/19 min；`wbgapi` 15/15；其余绝大多数 **<5 min**（nmc-weather 0.6、zgdypf-boxoffice 0.1）。法务线联邦成员（mfa-treaty-crawl 95.7 min 均值等）不属本仓排期体系。

**结论 B（真问题，已修）**：两个源的调度节奏**快于数据更新节奏**，产生无效抓取且消耗 fx01 代理流量：
| 源 | 数据频度 | 原调度 | 修正为 | 省略浪费 |
|---|---|---|---|---|
| `socrata-ny` | 周频（周一更新） | `3 5 * * *` 每日 | `3 5 * * 2` 周二 | 周 ~6 次 |
| `socrata-chicago` | 月频（月底发布） | `9 5 * * *` 每日 | `9 5 2 * *` 月 2 日 | 月 ~29 次 |

修正依据（数据实际更新时间的实测证据）已写入 manifest 注释；三闸全绿；60 天并发复验峰值仍 2 源（未引入新冲突）；`crawl_sources` 已镜像新 schedule。

**排除的项**：`amis-market`（monthly+yearly 双频）与 `usda-quickstats`（weekly+yearly 双频）经核为**多频源**，其 `dow=3`（周三）与 weekly 子口径相符，非错配。

**沉淀为不变量**：在产源调度节奏 SHALL 与声明数据频度相称（见主 spec `industry-source-expansion` 对应要求），声明的多频度以最高者为准。

### NFRA 金融监管总局通道打穿（2026-10-13，批次四留痕项 1 的深挖）

**背景**：批次四留痕的「NFRA 普惠金融监管统计」原判为「Angular SPA，后端接口未打穿」。本轮完整逆向，**后端通道已打通**（这是本次最有价值的产出）。

**通道（已实测可用）**：
- **后端 API 基址**：`https://www.nfra.gov.cn/cbircweb`（另有 `cbirczwzxweb` 同构镜像）。**原 `www.cbirc.gov.cn` 旧域名 DNS 已不通**。
- **可用端点**（均 GET，必须带 `Referer: https://www.nfra.gov.cn/` + `X-Requested-With: XMLHttpRequest`）：
  - `/DocInfo/SelectDocByItemIdAndChild?itemId=<栏目ID>&pageSize=50&pageIndex=1` → 文档列表 JSON（`{rptCode:200, data:{total, rows:[...]}}`，每条含 `docId/docTitle/publishDate/docFileUrl/pdfFileUrl`）
  - `/DocInfo/SelectByDocId?docId=<ID>` → 单篇详情
  - `/item/getItemBread?itemId=<ID>` → 栏目面包屑（可枚举栏目树）
  - `/item/getLeftMenuItem?itemID=<父ID>` → **完整栏目树**（注意参数名是 **`itemID` 大写 ID**，非 `itemId`）
  - `/item/getItemNameById?itemId=<ID>` → 栏目名
- **前端 CDN 静态 JSON 通道已废弃**：SPA 前端用 `originUrl + /cn/static/data` + `DocInfo_SelectDocByItemIdAndChild[itemId=X,pageIndex=Y,pageSize=Z].json` 的静态路径，实测全 404（改名后未重建），**但前端有 fallback 分支回退到 `/cbircweb/DocInfo/...`，后者有效**。
- **限流**：短时间内密集请求会 403（实测连续 5 页后触发），需间隔 ≥1.5s，恢复约 90s。

**关键栏目 ID**（本次枚举所得，避免重复劳动）：
| itemId | 栏目路径 |
|---|---|
| 953 | 统计数据（一级） |
| **954** | **统计数据 > 统计信息**（1382 条，含普惠口径） |
| 955 | 统计数据 > 数据图表（0 条） |
| 4234 | 专题专栏 > 推进普惠金融高质量发展（0 条） |
| 915/916 | 新闻资讯 > 监管动态 / 政策解读 |

**普惠口径实弹命中**（在 954 栏目前 7 页内检索 `普惠/小微/涉农/三农/县域` 命中 5 条）：
- `2026年银行业金融机构普惠型小微企业贷款情况表`（docId 1258118，doc/pdf 双格式）
- `2026年银行业金融机构普惠型涉农贷款情况表`（docId 1258117）
- 历史：2025 年度版（1208461/1209271）、2024 季度版（1164261）
- 数值实取（2026 年表）：银行业金融机构合计 387886 / 388792 亿元、大型商业银行 182411/184151、股份制 53288/52943、城市商业银行 48693/48563、农村金融机构 96214/95555

**决定性障碍（本次侦察的核心结论）**：**两个官方格式都不可直接解析**——
- **PDF 是纯图片扫描件**：实测 211KB，2 张 JPEG（`/Image`×2、`/DCTDecode`×1），**0 个 `/Font`**，`pdftotext` 输出为空，无文字层。
- **`.doc` 虽为 OLE2 容器但内容被 WPS 加密/混淆**：231KB→23KB（远小于 PDF，说明非图片），但 `file` 报 `Number of Words: 0 / Characters: 0`，`textutil -convert txt` 输出为空，UTF-16LE 中文串零命中（`strings -el`）。即 Word 数据流不可读。

**OCR 可行性实测（唯一可行路径，但精度不足）**：
- 本机有 `tesseract` 5.x + `chi_sim`/`chi_sim_vert` 语言包（163 语言），`pdftoppm` 可转图。
- 200dpi + `--psm 11`（稀疏文本）能出部分数值与中文；300dpi 对位改善（大型商业银行→182411/184151 可见）。
- **但表格行列对位不可靠**：200dpi 下「大型商业银行」「股份制商业银行」两行的数值缺失/错位，数值归属无法确定。

**平台既有文档能力盘点（2026-10-13，用户提示「office 套件时做过基础设施」后核实——结论：能力已有，不必自造）**：

| 层 | 组件 | 位置 | 对 NFRA 的价值 |
|---|---|---|---|
| ① 文档工坊 | doc-studio v1（谦面 pack `qnhd7B3J1-HKDDKzZQ_fUQ`） | paas 仓；执行层 python-docx/openpyxl/python-pptx/mammoth 进基础镜像 | 生成侧；含 `fetch_document_file` 资料库第四工具 |
| ② **MinerU 连接器** | `mineru.create_extract_task` / `create_extract_batch` / `get_extract_*` | **`open-connector-mt`（萬星的连接器载体）`src/providers/mineru/` + `catalog/apps/mineru.json`** | **关键**：支持 `is_ocr:true` + **`enable_table:true`（表格识别）** + `language:"ch"` + `model_version: pipeline/vlm/MinerU-HTML`；输入是**公网 URL**，正合 NFRA 的 pdfFileUrl |
| ③ MinerU 桌面版 | v0.14.1（VLM 模式，doclayout_yolo） | `~/MinerU/` | 实证：`.doc` → `_origin.pdf` → `full.md`(82KB) + `content_list_v2.json` + `images/`，**连 .doc 都能处理** |
| ④ 资料库工具 | document-library-tools | paas | 原件字节落工作区 |

**markitdown 否决实测（2026-10-13，用户问「markitdown 能实现这点吗」）**：
- 版本 0.1.6（已装）与 0.1.8（新装隔离目录）**两版结论一致**：NFRA 扫描 PDF → **输出 0 字符**（无 OCR 能力）；NFRA `.doc`（普惠小微 1258118、总资产月报两者）→ **`UnsupportedFormatException`（无 converter 尝试）**。
- **对照实验排除误判**：同一个 markitdown 对正常 `.docx` 输出 16 字符正常 → 失败源于 NFRA 文件本身（扫描件无文字层 / WPS 混淆 OLE2），非调用方式问题。
- 与文档工坊记忆一致：markitdown 在切片①即已出局（核心拖 magika→onnxruntime 80MB + pandas/numpy 105MB，对三格式零质量加成）。**解析侧不复用它**。

**结论修正**：NFRA 落地路径改为「NFRA 公告 API 取公网 pdfFileUrl → **MinerU 连接器**（is_ocr + enable_table + ch）→ 解析 Markdown/JSON 表格 → 结构化行」，**无需给爬虫镜像引入任何依赖**（外部服务调用，符合批次四 spec「不新建第三方依赖」）。**唯一未决项 = MinerU 有效 token**：桌面版配置里那条 `client_api_token` 实测 `user authenticate failed`（已失效），申请口径为 `mineru.net/apiManage/token`。
另建议：即便走 MinerU，仍用一期已知数值（如 387886 亿元）做 golden 锚，防表格对位漂移。
- **集群镜像未装 OCR**（Dockerfile 无 tesseract/paddleocr），平台无 OCR 先例——引入即新增依赖，违反「单元只依赖镜像预装」与批次四 spec「不新建第三方依赖」条款。

### 用户裁决（2026-10-13）：扫描件/表格 OCR 类源暂不处理

**裁决**：NFRA 这类**需 OCR 才能落地**的源（扫描 PDF / 混淆 .doc 内的表格），**暂不接入**，维持留痕。

**裁决依据（本次侦察的三条硬证据）**：
1. **两个官方格式都不可直接解析**——PDF 是纯图片扫描件（0 个 `/Font`，pdftotext 空）；`.doc` 是 WPS 混淆的 OLE2（`Number of Words: 0`，textutil/strings 均空）。
2. **通用解析工具不适用**——markitdown 0.1.6/0.1.8 对这两类文件分别输出 0 字符 / 抛 UnsupportedFormat（且对照实验证明非调用问题）。
3. **成本收益不匹配**：即便走 MinerU，仍需 ① 有效 token（当前无）② 逐期对位校验（OCR 表格行列易错，金融数据错一位即错数）③ 跨线调用（爬虫线消费萬星连接器）。收益为单源季度级数据。

**适用范围（推广为通用裁决，非仅 NFRA）**：
- **不接**：以扫描图片 / 加密混淆文档为唯一发布形态、且需 OCR 才能结构化的数据源。
- **例外（需重新裁决）**：若后续 MinerU 凭据到位、且目标源为高频高价值（月/周频、多领域复用），可重开——届时按「MinerU + golden 锚（已知期数值）+ 对位校验失败不出数」三件套实现。
- **不影响**：本次侦察所得 NFRA 后端 API 通道与栏目 ID 表**继续留痕有效**（条件具备时零成本复用）。

**剩余留痕项状态**（批次四三项）：①NFRA 普惠金融统计——通道已打通，按本裁决暂不接；②PBOC 贷款投向统计报告——改版待重新定位；③住建部住房公积金统计——数据序列待定位。

---

## 批次五：汽车与房地产行业分析口径（2026-10-13，change `inclusive-finance-expansion`）

批次四归档后同日的续探把三项待定项逐一钉死，并打通两个此前只到「站点可达」的行业口径源。**在产单元 105 → 107**。

### 新纳入两源（免 key、直连、已实测取数、已首爬）

| 单元 | 站点 | 通道 | 实测证据 |
|---|---|---|---|
| `cpcaauto-monthly` | 乘联会 `cpcaauto.com` | 发现 `news.php?types=csjd&page=N`（20 条/页，共 84 页）→ 正文 `newslist.php?types=csjd&id=<N>` 的 `div.read_content > div.text` | 2026年9月月度分析 10,240 字；含「零售 161.8 万辆，同比 −28.0%，环比 +5.0%」「新能源零售渗透率 67.0%」「出口 91.7 万辆，同比 +73.7%」 |
| `fangchan-market` | 中房协中房网 `fangchan.com` | 发现 `news.fangchan.com/api/newslist.json?subcolumn=原创&page=N&pagesize=M`（total 898，40 条/页，条目带 `url`）→ 正文详情页 `div.summary-text-p` | 2026-10-12 一文 1,852 字；含「50 城新增供应 1368 万㎡，环比 +103.6%」「成交 1020 万㎡，环比 +2.4%、同比 −20.1%」「二手房成交约为新房 1.4 倍」 |

**排期**：`20 6 * * *` / `46 6 * * *`（均每日，与实测发布节奏相称：乘联会 44 个发布日/68 天、中房网 38 个发布日/78 天）。经 60 天时长窗并发模拟零重叠——原候选 06:31 与 `elexon-bmrs`（33 6）、06:43 与 `afdc`（43 6 14）**撞窗**，已避。

### 两源坑位（复用时必看）

1. **cpcaauto 列表必须走 `news.php`**。`newslist.php?types=csjd` 不带 `id` 时返回 PHP 的 MySQL 报错壳（`Table 'cpca.ecs_books_csjd' doesn't exist` / `You have an error in your SQL syntax ... near ''`），**HTTP 仍是 200、长度约 496 字节**。带 `anid` 的变体（`news.php?types=csjd&anid=120`）实测 0 条，同不可用。
2. **cpcaauto 必须指纹伪装**。裸 UA 返回 33 字节「请使用浏览器访问本站」。`impersonate='chrome'`（本仓已有 4 个单元同机制）。
3. **cpcaauto 有 8/20 条图文报告**。首页 20 条抽样：12 条文本正文（928–10,235 字）、**8 条 `div.text` 内只有 `<img>`、文本 0 字**，集中在【联合发布】一周新车快讯 / 【新能源周报】/【商用车】周报 /【联合发布】OTA 监测月报。属用户 2026-10-13 OCR 裁决类，按规不处理——**首爬 60 条报告 → 31 行是预期行为**，不是漏抓。（我一度误判为「无间隔连发被节流」，复验推翻：加 0.4s 间隔后同样 31 行、同批 id 的图文报告仍 0 字。）
4. **fangchan 频道页主列表是 JS 空壳**。`/news/320/` 的 `<ul class="item-news-list"></ul>` 与 `<div class="page"></div>` 服务端为空，HTML 里只有右栏「更多」的 8 条时间线；**五种分页路径全 404**（`index_2.html`/`list_2.html`/`page/2.html`/`index_1.html`/`index_p2.html`）。内联脚本暴露真实数据源 = `news.fangchan.com/api/newslist.json`。
5. **fangchan 栏目实测**：原创 898 / 政策 7011 / 市场 3742；**数据·研究·年鉴·快报·测评·报告 六栏目 total=0**（入白名单只会得到空结果）。
6. **fangchan 正文要剥噪音**：正文在 `div.summary-text-p`，同页 `div.tubiaofenxian` / `div.wechat-share-pic`（含「扫描二维码分享」）会污染；`createtime` 是 **unix 秒字符串**（非 ISO），按 UTC+8 落日期。
7. **两源正文均为叙述文**（非结构化表）→ 单元**不抽数值**，`content` 存纯文本，口径靠 `report_title` + `publish_date` 锚定。强抽会把「同比 −28.0%」与「161.8 万辆」混入同列，语义不自洽。

### 留痕转轨道：四项「障碍 + 解锁条件」两段式

按批次五 spec 要求，每项写明**障碍**（可复现证据）与**解锁条件**（当前能否启动），不再写「不存在」：

**① NFRA 普惠贷款情况表** —— 定性已从批次四的「SPA 接口未打穿」**改写**为「接口已打通、障碍唯一」。
- 障碍：数据以 **PNG 图片**发布。`itemId=954`（统计信息，1382 条）内确有 `普惠型小微企业贷款情况表`（docId 1258118）、`普惠型涉农贷款情况表`（1258117）、`商业银行主要监管指标情况表`（1258121）；但 `SelectByDocId` 返回的 `docClob` 是 Word-HTML 导出，正文里**只有 1 个 `<img>`（如 `/chinese/OFFICE/HTML/1258118.files/12581180.png`）、0 个 `<table>`**。抽样 10 条（含月度/季度/保险/银行各类）**10/10 全为此形态**。
- 解锁条件：MinerU 凭据到位 + 用户对 OCR 类源的重开裁决。届时按「MinerU + golden 锚（如 387886 亿元）+ 对位失败不出数」三件套。

**② 住建部城市建设统计年鉴** —— **已解锁并交付**（2026-10-13，change `tabular-extraction-layer`）。
- 障碍（原）：内层为 **OLE2/BIFF `.xls`**（magic `d0cf11e0`）。`gongkai/fdzdgknr/sjfb/` 提供 2023/2024/2025 城建与城乡建设年鉴下载（合并版 2.26MB、47 sheets；分册 ZIP 内 90 个 `.xls`），但解析须 `xlrd`——爬虫镜像只装 scrapling 系，引入即运行时依赖决策。
- **解锁过程**：用户授权装依赖，但要求**做成通用能力**（"以后遇到类似情况也能解决，而不是只解决这次"）→ 建平台共享层 `fd_industry_data.tabular`（格式探测/xlsx/xls/html/zip/表头探测/CJK 表头清理），`xlrd>=2.0` 入镜像（96KB 纯 Python 零传递依赖），准入门新增 `inline-tabular-parser` 规则阻止第四份手写解析出现。
- **已交付**：`spiders/mohurd-yearbook`（在产，首爬 run 1961 success / 100 行 / 15s）。取合并年鉴「全国历年」11 表 + 分册 ZIP 村镇部分 `3-1-*`（建制镇/乡/村庄住宅·人口·建设投入——**普惠金融相关口径**）。
- **遗留**：年鉴为年刊，排期 `52 6 12 1 *`（每年 1 月 12 日）。

**③ 中汽协月度产销简析** —— 有列表、正文无数据。
- 障碍：`chn/4/cate_30/list_1.html` 条目可见（如「2026年8月汽车工业产销情况简析」），但文章正文实测 **912 字且无数据段**（数据在图片或附件内）。列表页本身另有 JS 渲染问题（首页 152 个 `con_` 链接多为导航）。
- 解锁条件：同 NFRA（MinerU 路径），或改接带数据的公开子栏目。

**④ 中国银行业协会理财市场指数** —— 值只在 PDF。
- 障碍：`Index/lists/catid/279.html`「理财市场指数报告」4 个年度分页可达、`Index/show/catid/280/id/46763.html` 正文 2,782 字**但只有指数定义说明**，数值在 8 个 PDF 附件（`/Uploads/ueditor/file/20261012/*.pdf`）。
- 解锁条件：引入 PDF 文本层解析——与批次四「公告类走文本通道」原则冲突，需另行裁决。

**其余复探结论（收敛为「已闭环」）**：
- **PBOC 贷款投向统计报告**：栏目已撤并，普惠口径并入金融统计数据报告（批次四 `pboc-inclusive` 已覆盖）→ 闭环，不再作为缺口。
- **住建部住房公积金统计**：统计栏目仅存《住房公积金统计调查制度》制度文件（有效期至 2030 年 7 月），无数据序列 → 闭环。
- **农口既有覆盖已够**：`agri-info`（农业信息网）/`amis-market`（G20 作物平衡）/`moa-hog-price`（生猪周报）/`fao-food-price`（FAO 粮价指数）四单元已在产；`zdscxx.moa.gov.cn`（重点农产品市场信息平台）与 `pfsc.agri.cn`（批发价 200 指数）实测需登录态/SPA，成本高于收益。
- **保险行业协会 `iachina.cn`**：栏目清晰（行业要闻/指数/研究报告）但无干净数据序列（行业指数栏目实为评论文章列表）。→ 排除，不列入解锁项。


---

## 平台通用表格抽取层（2026-10-13，change `tabular-extraction-layer`）

**缘起**：住建部年鉴（BIFF `.xls`）是批次五四项障碍之一，但侦察发现真问题不是「缺 xlrd」而是**缺一层通用抽取能力**，导致同一件事被反复手写。

**发现的三份手写实现**（准入门规则试跑时才发现第 3 份）：
| 单元 | 手写内容 | 缺失能力 |
|---|---|---|
| `pboc-monetary` | `read_sheet` + `_col_index` | 不支持 `inlineStr` |
| `pboc-inclusive` | `read_sheet` + `_col_index` | 不支持 `inlineStr` |
| `edgar-emissions` | `_shared_strings` + `_cell_text` + `_sheet_path` | 绑定单表名 |

三者互不兼容、各缺对方一半能力——第四个源来了只能再写第四份。

**共享层能力**（`fd_industry_data/tabular/`，随包进镜像，单元可 import，**不新建仓/镜像**）：
- `detect()` 格式探测**以内容为准**（扩展名不可信）：xlsx / xls(OLE2) / html / zip / csv；显式处理两类陷阱——**HTML 伪装成 `.xls`**（老站点常见）与 **zip 容器非 xlsx**（年鉴分册包）。
- `read_grid()` 统一二维字符串网格出口；`sheets()` 多表选择；`iter_rows()` 流式。
- `unzip()` **ZIP 文件名编码回退**：UTF-8 标志优先，否则 cp437→GBK。实测还原住建部乱码名（`2025─Ω│╟╧τ╜¿...` → `2025年城乡建设统计年鉴`）。
- `Table.find_header()` 支持**前置元信息行**（政府表格常态）；**定位失败即报错，不返回猜测列映射**。
- `squash_cjk()` / `strip_latin_runs()` / `is_latin_heavy()`：中文年鉴表头三坑——**中文对齐空格**（`供 水 普及率`）、**中英同格**（`统计个数(万个)\nNumber of\nTowns\n\n(10000 units)`）、**英文单位补注折行**（`(100 \nmillion persons)`）。剥离时**保留中文单位括号**。
- `fd_industry_data/http.py`：共享节流（`SAME_HOST_GAP_S` + `throttle`），替代 19 份手写。

**依赖决策**：`xlrd>=2.0`——96KB 纯 Python、**零传递依赖**；2.x 只读 `.xls`（xlsx 走 stdlib），互补不重复。对比 pandas 系（百 MB 级）是数量级差异。

**回接验证（行为不变由 golden 证明）**：三单元回接共享层后与回接前**逐一致**（`pboc-monetary` 50 行 / `pboc-inclusive` 60 行 / `edgar-emissions` 5 行，diffs 全空）；净删手写代码 1,430 + 1,381 + 1,557 字符。

**准入门规则**（让「通用」可执行）：`conformance_gate.py` 新增 `inline-tabular-parser`——单元内联手写 xlsx 解析（`sharedStrings.xml` / `xl/worksheets/` / 工作簿 `iterparse`）且未 import 共享层时报警。**只写文档约束不住**（三份手写实现就是在有规范的情况下出现的）；试跑即发现第 3 份，证明机械检查有效。

**对 `unified-source-onboarding` 契约的意义**：表格类源重新回到「只写源特定逻辑、不写解析器」；后续任何 BIFF `.xls` / 多表工作簿 / GBK ZIP 源可直接接入。

---

## 平台缺陷：声明参数在生产不可达（2026-10-13 修复）

**发现路径**：给 `fao-food-price` 加 `scope="annual"` 后要验证它在生产能跑，顺着 dispatcher 查参数通道，才发现这不是我这一个单元的问题。

**缺陷**：**49 个单元**在 manifest 里声明了 `limit` 之外的参数（`fao-food-price` 的 scope、`nbs-housing`/`mohurd-yearbook` 的 dataset、`usda-quickstats` 的 commodity/years/state、`un-comtrade` 的 reporter/period/…），但 dispatcher 构造 runner 命令时**只带 `--limit`**——这些参数在生产里**从未生效**，单元一律跑默认值。claim 时 params 明明被读出来了（`limit = params.get("limit") or 100`），却没往下传。

**修法**：
- `runner_cli` 新增 `--params '<json>'`：按**入口函数签名**过滤后透传。过滤是刻意的——manifest 与代码漂移应降级为「参数被忽略 + stderr 日志」，而不是 `TypeError` 炸掉整轮。**只认显式命名参数，`**kwargs` 不算声明**（否则拼错的键会被静默吞下，漂移不可见）。
- `dispatcher_cli` 把 claim 到的 params（除 limit 外）序列化进 `--params`。
- **k8s 分支（federated 成员）刻意不动**：其 command 由成员自持，追加参数有风险；平台原生源（`kind=platform`）全走 subprocess 路径。

**端到端实证**（不只单测）：写 `pending_runs(source=fao-food-price, params={"limit":40,"scope":"annual"})` → dispatcher tick 认领 → `fd-runner: fao-food-price -> success rows=40`（run #1967）——40 行正是请求的 limit，且是年度序列而非月度缺省。

**顺带发现的连带事故**：验证过程中 dispatcher 的 CronJob **卡在 ImagePullBackOff**，根因是它的镜像 tag `sha-92ae150` 已从 TCR 被清（tag 配额/保留策略），而 `kubectl set image` 只改了主容器、**initContainer `checkout` 仍指旧 tag** —— 必须两个容器一起改。已同步到 `sha-662b254` 并实跑验证。

**维护提示**：dispatcher 的 CronJob **不是 AppSet 管理的**（手工 apply），所以 AppSet 的 image 参数 patch 不会带上它——每次滚镜像要单独 `set image`（**两个容器**：`dispatcher` + `checkout`）。

### 参数通道连带审计：4 个休眠单元点亮即崩（2026-10-13）

--params 通道修通后，顺势审计「manifest 声明的参数 vs 入口实际收的」，查出更硬的缺陷。

**缺陷**：4 个单元入口**根本不接受 `limit`**——`gtarsc` / `hqcdc` / `intrinio` / `isee`，
入口是平台化之前的 scrapling Spider 脚手架形态 `run_<x>(urls=None, save=True)`
（返回值还是 `True/False` 而非 `list[dict]`，双重不合契约）。runner 恒定以
`fn(limit=...)` 调用，**一点亮就 TypeError**。因从未有排期、从未产生 crawl_runs，
问题一直不可见。

**新增 lint**：`check_manifest_commands.py` 第 4 条（runner 调用契约），三档口径：
- 在产单元违契 → **DRIFT（硬失败）**
- 已登记休眠违契 → HINT（提示，不拦构建）
- **未登记**休眠违契 → **DRIFT**（新漂移不可静默通过）

登记表 `scripts/runner-contract-dormant.txt` 写明移出条件与三条处置选项：
(a) 改造为内容单元（`run_<slug>(limit) -> list[dict]` + 三闸 + golden）；
(b) 判定不再需要 → 归档出 `spiders/`；(c) 仍需原 CLI 形态 → 登记为 federated
成员（自带 `runner_command`，不再受本契约约束）。

**2026-10-13 价值核查结论：四个都不值得恢复，建议退役**（用户问「休眠单元做什么的，
有价值吗，有价值就恢复」→ 逐条实测后答「无价值」）：

**共同形态（决定性）**：这四个不是四个独立源适配器，而是**同一个「大杂烩」通用爬虫
原型复制四份**——37 个域的 dispatch 列表**完全相同**，只有 `START_URLS` 不同；
52 个 `_extract_*` 方法里 **48 个是纯桩**（只取页面 `<title>` 与 meta description，
**不取任何数据**）；仅 ~4 个做表格抽取，且目标是 GitHub / UCI / FRED——这些我们
**已有专门在产单元**（fred-data 等）。37 域中 15 个已被在产单元覆盖
（fred-data / nbs-stats / mof / metal-com / cssn / cqvip / cap / bls / apipoer /
cisia / caa / agri-info / zce …）。

**逐条源可达性（实测）**：
| 单元 | 实测结果 | 判定 |
|---|---|---|
| `gtarsc` | 站点自述「该域名已不再使用，请访问 data.csmar.com」；后继 CSMAR 是**付费订阅**学术库 | 源已死，后继不可免 key |
| `hqcdc` | DNS **NXDOMAIN**（www 与裸域皆不存在） | 源已死 |
| `isee` | DNS **NXDOMAIN**（www 与裸域皆不存在） | 源已死 |
| `intrinio` | 站点存活但是**付费商业 API**（Pricing / Start Free Trial / Sign In） | 按「需注册 key 不接」裁决不合规 |

**故不恢复**。结论已写入 `scripts/runner-contract-dormant.txt`（避免后续重复侦察）。
若要清理，走 dormant-unit-hygiene 既有路径（归档至 `archive/<name>/spiders/`，
先例：flowers-yunnan → `archive/triage-cleanup-20261004/spiders/`）；在此之前保留
在册、仅 HINT 不拦构建。

**口径**：只对**新 schema**（有 `functions`）单元校验。旧 schema
（`eastmoney-data`/`eastmoney-futures`/`mysteel`/`worldsteel`，用
`commands`/`function_definitions`）走各自 `commands` 里的 shell 命令，不在本契约内。

**规则有效性已验证**（能真的失败才有价值）：探针在产违契 → exit 1；未登记休眠
违契 → exit 1；已登记 → HINT 且 exit 0。全仓 0 DRIFT + 4 HINT，**在产违契数为 0**，
故现在启用是安全的。

### 参数通道跨单元实证（2026-10-13）

不只 fao 一例。`mohurd-yearbook` 写 `params={"limit":25,"dataset":"rural"}` →
dispatcher 认领 → run **1971 得 25 行且 `crawl_items.payload->>'dataset'` 100% 为
`rural`**；对照 run 1970（无参）= `national` 50 + `rural` 50 交织。证明参数真的
生效（不是只看行数），且默认路径行为未变。同时在产单元 smoke（mohurd 100 行
success）确认共享代码路径改动无回归。

### 声明参数可达性全量审计 + 准入门新规则（2026-10-13，change `declared-param-reachability`）

**四单元已退役归档**（用户「好的，我接受」）：`gtarsc`/`hqcdc`/`intrinio`/`isee` 经
引用面体检（catalog/provider/sites.yaml/k8s/.github/docs/openspec 全净）后 `git mv`
至 `archive/triage-cleanup-20261013/spiders/`（git 记 rename，历史保留）+ INDEX.md；
登记表 `scripts/runner-contract-dormant.txt` 清空（移出条件已 met，今后新休眠违契
一律按 DRIFT 报告）。生产侧实证：dispatcher 空跑 `inventory synced, 104 source(s)`
（原 108），日志中四单元名 0 次出现；中央库 `crawl_sources` 删 4 行。

**全量静态审计**（97 个新 schema 单元，口径与 `runner_cli._split_params` 逐字一致：
只认显式命名，`**kwargs` 不算）查出并修掉：

| 单元 | 问题 | 处置 |
|---|---|---|
| `inmetals`/`kitco`/`metal-com` | 声明 `urls` 但入口 `run_x(limit)` 收不到 | **移除声明**（平台面从无此通道；是否开放任意 URL 抓取属政策裁决，不在本变更内。`mof` 的 `urls` 可达，保持不动） |
| `nbs-stats` | `parameters` **与 `columns` 都是字典形** | 改列表形——**此前该在产单元根本无法被协议加载**（`load_catalog` pydantic 直接拒）；`categories`/`start_year` 真的接到入口（缺省=原行为） |
| `cnia` | 声明的 `get_cnia_data` 带 `limit` 但该函数没有；真实入口 `run_cnia` 未声明 | 改为真实参数（`metals`/`include_reports`/`include_news`，**不含**反爬开关 `use_stealthy`）+ 补声明 `run_cnia` |
| `nbs_gdp` | `get_macro_data`/`get_gdp_quarterly` 的参数未声明（provider `introspect()` 早已广告） | 补声明（仅声明，无代码改动） |

**新准入门规则 `declared-param-reachability`**（`scripts/conformance_gate.py`）：AST
静态分析——gate 阶段只装 pyyaml，**不能 import 单元**（多数单元 import 即需
scrapling/scrapy/psycopg2）。校验 `parameters`/`columns` 列表形 + 声明名须在该
command 的 def 签名显式出现。**单向**：只查「声明了但收不到」，不查「收得到但未
声明」（回填类参数按 legal-line-federation 裁决刻意不上触发面，如 zgdypf-boxoffice
的 days/weeks）。规则有效性已探针验证（注入违规 → exit 1）。

**丢弃留痕**：被丢弃的键名写入 `crawl_runs.metrics.dropped_params`。**动因**=
`pending_runs` 有 **15 行**带 `{"limit":2000,"window":"12m"}`（2026-09-29，跨 8 单元），
全部报 `done`——`window` 既未声明也未接受，请求被无声忽略且不留任何痕迹。stderr
不够：dispatcher 以 `subprocess.run` 执行且不捕获它，输出随 Pod 消失。

**生产双实证**：`nbs-stats` 带 `{"categories":["gdp"],"start_year":2015}` → run 1977
日志显示**只请求 gdp 三类指标**（非全部五类）、URL 带 `2015`（非默认 2010）→ 参数
真的到达取数层；`mohurd-yearbook` 带 `{"window":"12m","nonsense":1}` → run 1978
`metrics={"dropped_params":["nonsense","window"]}`。

**未解决（留痕待裁）**：声明面更深一层——被声明的 `command` 能否被平台调用
（`IndustryDataProvider.run` 只分派 3 个 nbs_gdp 命令，其余单元的声明命令无平台调用
路径）。属声明面整体设计问题，涉及外部合同语义，未在本变更内处置。

### 声明命令可达性已收口（2026-10-13/14，change `declared-command-reachability`）

上面那条「未解决」已作为独立 change 处理完并归档。全量审计（口径 = 声明命令须是
`run_<slug>` 入口 / 在入口调用闭包内 / 在 provider 分派表）唯一违规 = **`eurostat-api`：
Wave C 四扩展（c20/bsci/apri/comext）有 golden 且全绿，但入口只遍历三条基础数据集，
`crawl_items` 零行**——golden 只证明「函数能跑」，不证明「生产会调用它」。

- **准入门新规则 `declared-command-reachability`**（AST 调用闭包）：`__main__` 块内调用
  不算平台调用面；**动态调用目标（`for fn in (...)`/`getattr`）报违规**，修法 = 显式按名调用。
- **修法**：三条同列集同语义扩展由入口显式调用；**comext 不并入**（`trade_value` 贸易额
  ≠ 指数语义，列集 15 vs 12）→ 入口末尾合并。**连带修掉 limit 饥饿**：顺序拼接 +
  CronJob `--limit 100` 让 `sts_inpr_m`（840 行）吃光额度，后两条每次定时运行零行
  → 轮转交织 + golden 006 跨数据集覆盖断言。
- **生产实证**：run 1985 rows=1998（原 878），DS-045409（comext）268 行首次入库。

### docker 站调度网格缺陷已收口（2026-10-14，change `fix-docker-schedule-grid`）

阈值校准线挖出的**静默生产缺陷**：`dispatch.enqueue_due` 回看步长 5 分钟，而 tick 只在
5 分边界跑 → 只采样与自身同余的分钟，`:51`/`:59`/`:39` 排期的源**永远不触发、零留痕**。
四源（inmetals/metal-com/eastmoney-futures/worldsteel）自 2026-10-02 断流 11 天，
巡检读不到证据 → 日更「证据不足」工单（校准期的 15 张修复单全部来自它们——
所谓「阈值过严」的样本其实是遥测缺失）。修为**逐分钟回看**。

- **关键坑：改在产源排期必须 manifest+push**——DB 直改 `crawl_sources.schedule` 无效，
  tick 每次先 `sync_sources` 用 manifest 覆写回（本次验证时踩实）。
- **三站镜像**：zihan/xinru-server2 的 `/opt/fd-dispatcher/run.sh` 引用 tag 本身，
  tick 时 `docker run` 自动拉新（实测 36 分钟内到位）；xinru-server1 是 k8s CronJob
  （无 initContainer）`set image`。
- **实证**：metal-com 临时改 16:29 → pending 164 `requested_by=schedule-tick` 16:30 入队；
  校准补跑单 → run 1988-1991 四源全 success（11 天断流后恢复）。



- 2026-10-21 **产品面接入（industry-vertical-supply）**：14 个既有单元的数据第一次对客户可见——`crawl_items` 回补进 `semantic_observations`（2,997 行）→ 86 个语义码登记（85 命名层 + 事实占比，70 个过了命名门进 `registry_entries`/`indicator_snapshots`，wire 侧 verified 70）→ 四个行业看板上架 `#/showcase`（anonymous 可见）。**各源新披露的指标与限制**：spb-express=业务量/收入 YTD（2022-10 起，2023-05…12 单月口径期已排除、缺口 34/29 期）+ CR8（2013-05 起 153 期，2026-03 口径切换 87.3→96.0）；chinawuliu=LPI 11 期（稀疏、期号错位按源字段）+ 电商指数 7 期 + 公路运价 20 个报告日点（非连续周线）；portwatch=港口横截面（仅 3 快照日，按港口行本批无实体归宿未回补，登记延后）；carbon-monitor=CO2 分部门日排放（仅 2 快照日、Mt→Gg、EU27/ROW 聚合行排除，横截面不出趋势）；ember=德国发电量/占比（仅 DEU 5 个月，上游 2015-01 起待回补）；eia-v2=CISO 小时需求/预测/净发电/交换（仅 CISO、滚动短窗、只作日型）；entsoe-e=CZ 分燃料 15 分钟功率（单 bidding zone 5 天）；edgar=阿鲁巴 2 部门 56 年（D5 降级非看板源）；nifdc=批签发周计数（签发窗文本归一 ISO 周、13 锚点 7 周、limit 截断）；openfda=美国不良事件月计数（100 月连续）；clinicaltrials=注册月计数（100 去重月、全球库按归属国聚合）；zgdypf=全国大盘日票房双口径（28 自然日、同日两行取 scraped_at 最新、分账约为含服务费 90–92%）；boxofficomojo=年度榜（按影片行无实体归宿未回补）；steam-ccu=累计评测/瞬时 CCU（按游戏行无实体归宿未回补）。**口径红线**：全程不插值不补零、同日重复行按规则去重、浅源只作横截面不出两点趋势

---

# 银行业专场 Wave（2026-11-07，12 路 = 10 外部 + 2 内部）

> 缘起：用户开「银行业数据线」（调研→爬虫平台→柏讯资源→看板→监控预警）。范围=官方监管统计/处罚、央行信贷口径、货币市场、债券与资本工具、协会理财、A 股+H 股银行披露、评级、不良转让。
> **车道裁定（本波两条裁决之一，见下）**：银行财报（定期报告）属 cn-report 线（`unified-source-onboarding`/`industry-source-expansion` 明文排除财报邻域进 industry 批次）；本波 industry 候选均为非财报源。财报侧通道验证（巨潮/披露易）一并留档本节供 cn-report 线复用。

## 星接候选总表（25 源，全部直连、免 key、无需代理）

| # | 源 | 方向 | 端点要点 | 鉴权 | 周期 | 成本 |
|---|---|---|---|---|---|---|
| 1 | NFRA 统计 Excel 附件 | 行业面 | `SelectByDocId?docId=` → `attachmentInfoVOList[].urlOtherName` → `/chinese/docfile/<年>/<uuid>.xls`（BIFF8，**裸请求 206 无鉴权**） | 无 | 季/月 | S |
| 2 | NFRA 处罚公开 | 企业面 | `/cbircweb/DocInfo/SelectDocByItemIdAndChild?itemId=` 叶子 4113(总局662)/4114(监管局本级33,000)/4115(分局41,918)；各机构树 1000→1030/1031/4311 | 无(双头) | 日 | S |
| 3 | PBoC 信贷收支表 | 行业面 | `diaochatongjisi/116219/116319/<年>ntjsj/jrjgxdsztj/` 静态页内嵌 9 表 xlsx 直链（`attachDir/YYYY/MM/<id>.xlsx`），2016 起，四类银行分列 | 无 | 月 | S |
| 4 | PBoC 贷款投向 | 行业面 | `goutongjiaoliu/113456/113469/` 季度新闻稿（2026-10 复测新址；2026Q3 实测含普惠小微 38.50 万亿/涉农 54.29 万亿） | 无 | 季 | S |
| 5 | PBoC 货政报告 | 行业面 | `zhengcehuobisi/125207/125227/125957/` 议题页单 PDF，2001–2026 全序列 | 无 | 季 | S |
| 6 | PBoC 区域金融 | 区域 | 年度合辑页 33 个 PDF（主报告+31 省+深圳摘要），另有各省分行子域全文页 | 无 | 年 | M |
| 7 | LPR | 货币市场 | `GET chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHisExcel?lang=CN` 全史 xlsx 1540 期（2013-10-25 起）；`LprHis` JSON 恒钳近 12 期只作增量探针 | 无 | 月 | S |
| 8 | Shibor | 货币市场 | `POST /ags/ms/cm-u-bk-shibor/ShiborHis`（**必须 POST**，参数在 query）全史 2006-10-08 起，窗口 ≤1 年分片；`ShiborPriHis` 报价行明细（memCode=`\|`拼接串） | 无 | 日 | S |
| 9 | FR/FDR | 货币市场 | `POST .../FrrHis` + 静态 `/r/cms/www/chinamoney/data/currency/frr-chrt.csv`、`fdr-chrt.csv` | 无 | 日 | S |
| 10 | NCD AAA 曲线 | 货币市场 | `GET /ags/ms/cm-u-bk-currency/ClsYldCurvHis?bondType=CYCC41B`（曲线码表 `ClsYldCurvCurvGO`）——**线上仅滚动 ~2 个月**，须自累积 | 无 | 日 | S |
| 11 | 上清所月报 | 行业面 | `POST /shchapp/web/sdocClient/monthListPage`（JSESSIONID+Referer，channelId=ff80808140a43ba80140a45b17320007）表四托管/表五持有结构，2014-12 起 | 匿名cookie | 月 | M |
| 12 | 中债登统计月报 | 行业面 | `POST chinabond.com.cn/cbiw/GetMonthReport/queryContent`（ywbbnr=base64 PDF 内联）+ `GetDataByte`（sWjlx=3 xlsx），**1997-01 起**，8 表含持有者结构 | 无(XRW头) | 月 | S |
| 13 | 中债收益率曲线 | 市场面 | `GET yield.chinabond.com.cn/cbweb-mn/yc/downYearBzqx?year=&ycDefId=` 整年包 + `queryTree` 160+ 曲线——**含商业银行二级资本债收益率曲线 AAA-至A** 等资本工具曲线 | 无(Referer) | 日 | S |
| 14 | 上清所 TRS 公告 | 资本工具 | `POST /shchapp/web/disclosureForTrsServer/search`（ch166 流通要素/ch144 发行/ch177 评级）；流通要素详情页 HTML 自带代码/总额/期限/票面利率/评级 | 无(Referer) | 实时 | S |
| 15 | CBA 理财指数 | 理财 | `china-cba.net/Index/show/catid/280/id/{46763=2026,44625=2025,43220=2024,38855=2022-23}` 附件 **PDF 有文本层**（53 期，2022-02 起；2022-25 为 docx 更好抽） | 无 | 月 | S/M |
| 16 | 中国理财网报告 | 理财 | `chinawealth.com.cn/lc_lcsj/lcbg/` 28 期（2013 起），PDF 在详情页 `data-recurl` 属性 | 无 | 季 | S |
| 17 | 理财产品查询 | 理财 | `POST /lcw-fe-service/m/n`（body=RSA 公钥裸 base64）→`/prod/search`（**AES-256-ECB**+头 X-Timestamp/X-Nonce/X-Sign=SHA256(`data=<ct>&nonce=<n>&timestamp=<t>&signKey=ppnn13%dkstFeb.1st`)） | 免登录 | 实时 | M |
| 18 | 东财披露日历 | 预警 | `GET datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_PUBLIC_BS_APPOIN`（FIRST_APPOINT_DATE/CHANGE/ACTUAL 三列，回溯 2007，`in` 批量）——「到期未披露」预警数据源 | 无 | 随披露 | S |
| 19 | 港交所披露易 | 企业面(H股) | `www1.hkexnews.hk/search/prefix.do`（代码→stockId）+ `titleSearchServlet.do`（列表，YYYYMMDD，t1code=40000 财报/t2Gcode 预警类目）+ PDF 直链；类目树/活跃证券静态 JSON | 无 | 日 | S |
| 20 | 中诚信国际 | 评级 | `website-api.ccxi.com.cn/admin/content/{dqgz,cspj,bdqgz}/page`（HMAC-SHA256 签名，钥硬编码前端 app.js 已复现；银行跟踪 3,983 条；PDF 直链 OSS 免签名） | 无 | 日 | S |
| 21 | 大公国际 | 评级 | `POST dagongcredit.com/api/construction/openApi/getContentInfoPageList`（**无鉴权**，topic="商业银行" 94 条，a1=PDF 直链） | 无 | 日 | S |
| 22 | 联合资信 | 评级 | `lhratings.com/lists/111.html?p=N`（2,927 页静态）+ `?title=银行` | 无 | 日 | S |
| 23 | 东方金诚 | 评级 | `dfratings.com/Periodic-tracking.html?page=N` + `?wd=银行` | 无 | 日 | S |
| 24 | 上海新世纪 | 评级 | `http://shxsj.com/serve/api/article_api/get_cid_article`（**仅 HTTP**，cid=50，银行 1,081 条，pdf[] 附件对象） | 无 | 日 | S |
| 25 | 银登不良转让 | 资产质量 | `yindeng.com.cn/ywzq/ywzq_bldkzr/bldkzr_xxpl/bldkzr_xxpl_zrgg/`（挂牌 6,155 条）+ `..._zrjggg/`（成交 3,030 条，2021 试点起）；PDF 文本层含笔数/户数/未偿本息/加权逾期天数/五级分类 | 无 | 实时 | S-M |

（A 股银行公告通道一条，属 **cn-report 车道**：巨潮 `POST /new/hisAnnouncement/query`（category 四类定期报告）+ `www.cninfo.com.cn/new/data/szse_stock.json` orgId 官方映射 + `static.cninfo.com.cn/finalpage/` PDF 直链（支持 Range）+ 东财 `np-anotice-stock`（列表）/`np-cnotice-stock`（正文桥接，5000 字/页翻页拼接）。）

## 裁决记录（本波两条）

1. **NFRA「扫描件暂不接」裁决（2026-10-13）事实前提变化**：当时认定统计表唯一可行路径=OCR（PDF 纯图片/doc 混淆，三条硬证据留痕批次四）。本波实测 `SelectByDocId.attachmentInfoVOList` 每期携带 **Excel 附件直链**（BIFF8 真实 biff，无鉴权），商业银行主要监管指标/分机构类/普惠两表/月度总资产负债 4+ 期连续验证全有——**无需 OCR、不触及裁决原文**（裁决对象是「需 OCR 才能结构化」的源），NFRA 统计表回归可接。原裁决记录保留效力：若附件通道未来断供，OCR 三件套（MinerU token+golden 锚+对位失败不出数）仍是唯一解锁路径。
2. **财报邻域车道**：42 家 A 股银行定期报告监控走 cn-report 线（fd-cn-report ingest 唤醒 + `cn-report-incremental-crawl` 水位线），不进 industry 批次——与 2026-10-07「SEC 维持排除（与已有财报重叠）」同构：排除的是 industry 批次重复接财报，不是财报能力本身。

## 内部盘点（路 11/12，立项依据）

- **fd-cn-report 库为空**：daas.db（`sqlite3 "file:...daas.db?mode=ro"`）`report_documents`/`report_sections`/`es_index_meta`/`taxonomy_mapping` 全部 **0 行**；llm_rules 3,389 + script_rules 5,553。银行覆盖=26 条 bank-scoped LLM 规则（25 条 sub_types=`*`）+180 条 801780（申万银行）script 规则；监管核心指标组（NIM/净利差/不良率/不良余额/拨备覆盖率/拨贷比/贷款拨备率/资本充足率/核心一级/一级/LCR/四级迁徙/逾期率/重组率/风险加权资产）**~70-80% 已有规则**；缺 NSFR/杠杆率/客户集中度/成本收入比 scoped 版（存贷比 2015 废止不必补）。**真正缺口=ingest 唤醒**：巨潮→入库→切章→抽取→落库链从未在规模上跑过；唯一银行痕迹=`fd-cn-report/out/601398_2023.json` 测试产物（4 期提取，仅 5 指标/份）。规则有效性未经在库验证。
- **机制锚点在册**：看板=`dashboards/data_plane.py`（四后端，未登记快照拒绝，SeriesError 禁空图）+`public_projection.py`（FORBIDDEN 正则闸）+`dashboard-publication` 红线（禁内部标识/口径声明/覆盖省数声明/as-of 机器派生）；监测舰=`fleet-packs/blueprints/schema.md` 蓝图 v2（monitoring.escalate 走拍板不自决+五型 acceptance；范本 cross-border-ecom-policy）；指标登记=`industry-observation-supply`（键 (concept_id,entity_type,entity_id,date,granularity,source_used)，不插值不补零）+`unified-indicator-registry`（命名门=semantic_code+中英名+unit+frequency 缺一 unverified 即对读取面不可见）；财报增量=`cn-report-incremental-crawl`（per-concept 水位线→CrawlPlan→幂等 upsert）；conformance gate 现行检查项在 `fd-industry-data/scripts/conformance_gate.py`。

## 各路坑位（适配器建造必读）

### 路 1 NFRA 统计
- pageSize 无视传参恒返 20/页（954 栏目 1,386 条≈70 页）；docClob 嵌 Word-HTML 含未转义控制字符，须 `json.loads(strict=False)`
- 月度总资产负债表=**同 docId 原位更新**（年度一个 docId 如 1265692，publishDate=最近月度刷新；attachment uuid 月度轮换——必须每次重查详情拿最新直链，勿缓存）
- 标题口径漂移：2024/2025 期带「（季度）」后缀、2026 期无；银行季度批量 2024/2025 每年只发 2 月一次、2026 改 2 月+8 月——按标题去重/推周期会翻车；发布日历基准=《监管统计信息发布日程表》docId 1249748
- xls=BIFF8（走 `fd_industry_data.tabular`/xlrd 路线）；PDF/DOC 正文全 PNG（pdftotext 空）；955 图表栏目文档数 0、静态页 404（SPA 路由）

### 路 2 NFRA 处罚
- 必带 `Referer: https://www.nfra.gov.cn/` + `X-Requested-With: XMLHttpRequest` 双头；突发限流返回 `msg:"未知错误"` HTTP 200 假象（p1 因 CDN 缓存限流期仍活，误导排障）——判据 `rptCode!=200` 退避 ≥90s
- 931 聚合栏目排序异常（p1 升序 2018-12 起）且 total(144,820)≠叶子之和(150,501)——**监控只打叶子**；支局级 4292 全局仅 2 条勿建通道
- 服务端检索=零（searchkey/publishDateBegin/End 均被忽略，total 不变）——按银行/机关/日期过滤全在本地做；pageSize>20 静默截断为 20
- 双格式并存：旧文档 docClob=Word 导出 HTML（剥 MSO CSS/gb2312），NFRA 时期=「公示列表」批量 PDF 表（`pdftotext -layout` 切行，一表多案，如兴业 695 万/光大 180 万）；新文档 pdfFileUrl 路径可预测 `/chinese/OFFICE/PDF/<docId>.pdf`
- www.cbirc.gov.cn 域名已注销（NXDOMAIN 无 301）；历史深度翻到末页：4113=2006-03、4293=2003-10（银监会时代）

### 路 3 PBoC
- 116225 是混合扁平目录（月度数据报告/地区社融/小贷季报/2011-18 旧贷款投向混住），文章 id「14 位时间戳串/纯数字/32 位 hex」三形态混杂只能按标题匹配；goutongjiaoliu 迁移件 URL 时间戳失真（发布日期取正文「文章来源」字段）
- 信贷收支表 xlsx：月份表头数字截零（`2026.1`=10 月）、sharedStrings 带 `\xa0` 中英双行、首 5 行行号噪音；栏目在线深度止于 2016（2015 年页无此子栏目）
- 货政报告无 xlsx 附件（统计附表在 PDF 内）；Q3 报告发布晚于贷款投向（2026Q3 于 11-07 未出属正常）；`/eportal/ui` AJAX 端点不存在，列表走静态文章页
- 央行 LPR 栏目 404——LPR 以 chinamoney 为准；站内搜索引擎 `wzdig.pbc.gov.cn/search/pcRender` 可作栏目改版兜底发现层（不宜做主通道）

### 路 4 货币市场
- **chinamoney 假 200**：频控返回 HTTP 200+HTML 403 页（`<title>403错误</title>`），按「请求指纹」记名封禁（同参数组合反复 403、换参数组合立即恢复）——必须检查响应体是否 JSON；端点间隔 ≥3-5s
- ShiborHis/ShiborPriHis 必须 POST（GET 返无记录壳）；akshare 老路径 `cm-u-bk-currency/ShiborHis` 已 404，正确模块前缀 `cm-u-bk-shibor`
- 窗口硬限 ≤1 年，超窗**静默返回空 records**（不报错）——全史按年分片（2006 分片已验证）；`ShiborMnHis` 月均值两种日期格式均空 records（建议日频自聚合）
- shibor.org DNS 已死（SERVFAIL）、shibor.org.cn 停放域名（Vultr IP+parking 页）勿用；`/chinese/bkcurv/` 空壳
- 上清所三重门：无 JSESSIONID 302 error.jsp→带 cookie 无 Referer 空 success→附件无 Referer「页面不存在」；Content-Type 撒谎必须魔数验文件；channelId=app 树（ff80…0007 统计月报），与 TRS web 树 ID 体系不同勿混用；2025 后文章页有静态 `P*.pdf` 直链可跳过三重门，2014-12~2024 归档只能走 sattaClient/download

### 路 5 债券/资本工具（重跑）
- chinabond `GetDataByte` 的 sCode 与页面序号差一位（sCode=04 返第 6 张「主要券种持有者结构」）；新月份 queryContent 的 bbbh=null——按月缓存映射或 1..8 枚举
- `searchYc` 老端点已死（返错误页 HTML），现行 `ycDetail`（单日，workTime 必锁日期防默认漂移）/`downYearBzqx`（整年包）；曲线 xlsx sharedStrings 为空、字符串内联 sheet XML（解析器须兼容 inline str）
- 检索词口径：上清所标题里永续债叫「**无固定期限资本债券**」（搜「永续债」0 条）；ch166 搜「二级资本债券」2026 年 50 条、「无固定期限」64 条
- TRS search 不带 channelId 报错「请选择查询的栏目」；日期+keyword 部分组合 success:true total:0——用宽词+本地过滤日期；`www.shclearing.com`（无 .cn）DNS 不存在

### 路 6 协会/理财
- CBA 附件 URL 的日期目录=上传批次日**非报告期**（同年各月分属不同批次目录）——必须解析年度详情页完整 href，不能拼规则；2022–2025 为 docx（zipfile+document.xml 比 PDF 好抽）、2026 才换 PDF；catid/279 历史遗留 302→280
- 当前理财指数序列**无风险/转型指数**（2022-02 定义=现金管理收益+六个月价格+一年价格三类；2026 格式=现金管理+固收类收益指数短/中/长期），数值在正文叙述可正则抽取、图表为图片；数据支持方=普益标准
- chinawealth 报告 PDF 链在详情页 `data-recurl` 属性不在 `<a href>`；列表页码 JS 生成；`/m/n` 响应=裸 base64 字符串非 JSON；AES 必须 256（128 返「发生异常」）；X-Sign 拼串按字母序 data/nonce/timestamp+signKey；`/prod/search` 服务端 429 频控（RSA-1024 握手每会话一次可缓存 key）
- 死胡同：chinawealth 信息披露内容通道 401（需注册）；CBA 年度报告无公开统计附录（详情页只有活动照片）

### 路 7 巨潮 A 股银行
- **orgId 不能拼接必须查表**（`szse_stock.json` 免鉴权 ~5k 条，启动时拉取+定期刷新）：工农中=`jjxt` 前缀、建行=`9900` 前缀、深市多=`gssz`——42/42 全命中
- **category 无效时静默降级**：`category_yjkb_szsh`（业绩快报）被忽略返全量（工行 258 条含制度/决议杂项）——快报必须走 `searchkey=业绩快报`；接入后必须校验返回条数符合类目预期（年报≈2 条/年，200+=过滤失效误入库）
- 东财正文每页 5000 字符（三季报 12 页，年报更多），按响应 page_size 循环翻页拼接；国有大行 A+H 双版本须按「含 H股公告」去重（否则年报计数翻倍）；年报标题混用「年度/年年度」两写法，半年报出现无「年」字（「2026半年度报告」）
- 业绩快报覆盖不均：招行/平安/兴业等股份行 1 月发、**工农中建从不发**——预警引擎不能做「快报到期未披露」只能做「事件到达」；银行无月度经营披露义务（经营月报全市场 0 条）；银行基本不发业绩预告
- 分红已半年化（招行 2025 年度起半年度分红）——分红监控不能只盯年报后 5-7 月窗口；`category_qyfpxzcs_szsh` 过滤精准（招行 8 条）
- RPT_PUBLIC_BS_APPOIN filter 须整体 urlencode（编码不全返非 JSON/连接重置）；巨潮无「预约披露」公开 API（两路径 404）；东财公告列表（工行 total_hits 2,234）可作巨潮限频时「新公告到达」兜底监控

### 路 8 披露易（H 股）
- 个股过滤必须 prefix.do 解析 stockId（`stockcode` 参数无效返全市场；activestock JSON 的 `s` 字段是旧 ID 空间，servlet 不认且会**错位到别的公司**——危险）
- 日期参数必须 YYYYMMDD（`07/11/2025` 返 result:"null"）；响应 `result` 是二次转义 JSON 双重解析；`rowRange` 上限 1000（靠收窄日期窗，TOTAL_COUNT 判截断）；STOCK_CODE 可能 `<br/>` 多码
- HEAD 对 www1 返 503 假象（GET 正常）——拨测用 GET 看响应体；「全类目 1 月/单类目 12 月」是前端限制，服务端实测 34 个月跨度通（可利用勿依赖）
- 纯 H 银行无季报（40300/13600 类目 2020-2026 恒空——勿以类目存在推断有数据）；披露节奏=年度业绩公告(3 月末)→年报(4 月末)→中期业绩(8 月末)→中报(9 月)；日常预警可走**全市场日更扫描**（stockId=-1+类目+日期，每日 1 请求覆盖 16 家）
- 停牌股盛京 2066/九台农商 6122 无 API 索引（type=I 任何时段 0 条）；已退市代码仍在 inactivestock JSON 勿误当在市；13100 董事会日期预告覆盖不全（业绩日期预警不能只靠它）

### 路 9 评级
- 中诚信签名=「前端藏钥」型（HMAC-SHA256，钥硬编码 app.js，已复现 Python 版）——**钥换版即批量失效，签名逻辑须做成可配置**；同一报告按所覆盖每只债重复一行（按 ratingreport URL 去重）；主动评级走付费墙但银行所在的 dqgz/cspj/bdqgz 主库免费
- 大公：真实域 `dagongcredit.com`（dagong.com NXDOMAIN）；`searchTitle` 参数无效，银行检索必须 `topic` 字段
- 联合：必须 `lhratings.com`（lianheratings.com.cn TLS 证书不匹配）；新世纪：**只能 HTTP**（443 不通），pdftotext 偶发字间空格（匹配前去空格）
- 上清所 177 频道（评级公告 40,536 条，keyword=银行 909 条）列表免费，附件 PDF 需登录（download.jsp→loginerror）；多关键词 OR 逻辑（AND 本地过滤）

### 路 10 银登
- 旧域名 lcidrc.com DNS 已死，唯一官网 yindeng.com.cn（官方防冒名声明）；`/xxpl/` 一级栏目有登录墙（Ydw-Token）但**不良转让系列完全公开**，双路径别名（`/xxpl/xxpl_bldkzr_*` 与 `/ywzq/ywzq_bldkzr_*`）均可直连
- 公告 PDF 混入竖排水印（「未经许可不得转载」逐字断行——正则剔除单字行）；2024-12 改版 URL 日期失真（发布时间取页面字段）
- 季度统计序列只剩媒体转述（官方已调整披露渠道，年报明言）；金交所 25 家全灭（北金所 2024-08 退出地方交易场业务；死所域名被停放/抢注——大连 djfae.com 已是 AWS 停放页，旧清单域名勿直接入库）；京东拍卖登录墙；中债-银登指数（`yield.chinabond.com.cn/cbweb-mn/ydw/ydwIndexInit`，indexid=8a8b2cef6c978331016c985935020006）1487 点止于 2024-12-12 疑停更

## 名单核实（本波全量核实产物）

- **A 股 42 家**（东财 BK0475 total=42，33 沪+9 深）：沪=601398 工商/601288 农业/601988 中国/601939 建设/601328 交通/601658 邮储/600036 招商/601166 兴业/601998 中信/600016 民生/601818 光大/600000 浦发/600015 华夏/601916 浙商/601838 成都/601860 紫金/603323 苏农/600919 江苏/600926 杭州/600928 西安/600908 无锡/601009 南京/601169 北京/601187 厦门/601229 上海/601128 常熟/601077 渝农商/601825 沪农商/601997 贵阳/601963 重庆/601665 齐鲁/601577 长沙/601528 瑞丰；深=002142 宁波/000001 平安/001227 兰州/002807 江阴/002839 张家港行/002966 苏州/002948 青岛/002936 郑州/002958 青农商行（生产清单以工具实时拉取为准，orgId 一律走 szse_stock.json）
- **纯 H 股 15 家活跃**（prefix.do 逐一核实）：6138 哈尔滨/2139 甘肃/6190 九江/2558 晋商/1983 泸州/9677 威海/9889 东莞农商/1551 广州农商/1578 天津/1216 中原/1916 江西/6199 贵州/3698 徽商/9668 渤海/2596 宜宾（2025-01 上市，新名单易漏）；停牌 2 家=2066 盛京/6122 九台农商；已退市=416 锦州；A+H 15 家走 A 股通道即可

## 留痕三项（障碍+解锁条件两段式）

1. **银行资本债「不赎回」公告无干净结构化通道**：上清所 TRS 全时段 ch166 0 条+ch177 仅 2 条无关（2019/20 中票关注公告）。推进口径=A 股银行走巨潮 searchkey（「二级资本债券」已验证：建行 11 条含发行完毕/赎回完成）+H 股走披露易类目；纯银行间发行（非上市银行）发行人无强披露义务——按「上市银行全覆盖、非上市挂起」口径。
2. **NCD AAA 收益率曲线线上仅滚动 ~2 个月**：历史不可回补。解锁条件=接入即开始日更累积（宜早不宜迟）；或经上清所月报表四做月频近似。
3. **中债-银登信贷资产价格指数疑停更**（1487 点止于 2024-12-12）：接入前先复核活性；确认停更则按横截面/历史快照口径登记，不注册成长序列。

## 监控预警层映射（车道 C，全部复用既有机械）

- 披露日历预警=东财 RPT_PUBLIC_BS_APPOIN（actual=null 且过预约日→逾期；注意 filter 编码坑）
- 事件流=NFRA 处罚叶子栏目增量 / 披露易 t2code（13300 末期业绩/13400 中期业绩/13250 股息/12350 更换董事/13200 延迟发表业绩）/ 银登新挂牌 / 五家评级机构日更
- 指标阈值巡检=cn-report 抽取指标落 semantic_observations 后按「指标+阈值+窗口」配置巡检（不良率环比跳升/拨备覆盖率破 120%/NIM 连续 N 季下行/资本充足率逼近监管线）——通用能力，各行业可复用
- 数据源断流=gap_in_series/crawl-run-telemetry/巡检班既有机械，与全仓一致

## Wave 日志
- 2026-11-07 银行业专场 12 路（10 外部+2 内部）并行派出，全部完成。星接 25 源全部直连免 key（本机代理 7890 端口未开，无代理轨道需求）。路 5 首跑输出失控（18M tokens 复读循环、无报告产出，转存文件仅可回收开头数 KB），当日按收紧纪律（探测点 ≤8/单点 ≤3 试/报告 ≤120 行）重跑完成。两条裁决+两项内部硬结论（fd-cn-report 库空→ingest 唤醒是真缺口；机制锚点全在册）见上文。落地批次未派，待用户立项（车道 A 批次接入 / 车道 B 财报唤醒 / 车道 C 预警层）。

---

# 餐饮行业专场（2026-11-07，change `add-restaurant-vertical` 波1）

> 详情三份：`data-source-scouting/restaurant/{ico-coffee-price,restaurant-rpi,samr-food-inspection}-scouting.md`
> 建单产物：`fd-industry-data/spiders/{ico-coffee-price,restaurant-rpi,samr-food-inspection}/`
> 三源全部**直连可达、免鉴权**（本机实测；本机代理 7890 当日未开，无代理轨道需求）。

**接入状态（task 2.3 收口，2026-11-07 查库实证）**

| 源 | 试跑 | 点亮 | 首批观测入库 | 口径守卫基线 |
|---|---|---|---|---|
| `ico-coffee-price` | success rows=285 | manifest `schedule: 23 6 * * *` | ✅ 1,425 行 / 5 概念（窗口 2025-09→2026-11，5 条 indicator 全过命名门） | 列序守卫：Robustas 恒最低 + I-CIP 落在四分项区间内；**实测 2026-04-07 Other Milds > Colombian**，故未采用「Colombian 恒最高」这条看似合理的规则（否则误判真数据） |
| `restaurant-rpi` | success rows=5 | manifest `schedule: 41 5 2 * *` | ❌ **0 行（诚实不入库）**：单版 PDF 仅滚动 5 个月窗，5 < 24 期趋势门 → 抽取器 SKIP 并记录真实期数，历史靠月度累积 | 三重交叉核对：同版 rpi / current / expectations 与官方页正文一致（2026-09 = 100.7 × 3） |
| `samr-food-inspection` | success rows=100 | manifest `schedule: 27 6 * * 3` | ✅ 69 行 / 2 概念（不合格通报条数 2022-01→2026-10 共 43 真实月；餐饮相关 26 真实月） | 字段级口径落 `fd-industry-data/docs/samr-restaurant-caliber.md`：三分类 + 命中词表 + **公告条数≠不合格批次数** + 缺失月不补 0 |

> 「点亮」= manifest 的 `schedule` 字段（仓内真源）。**上产（push → CI 出镜像 → 集群滚版）尚未执行**，
> 属 change 挂账项，不在侦察簿内自行宣告完成。

### 路 1 ICO 咖啡指标价（`ico-coffee-price`）
- 数据面已从 CSV 迁到门户 JSON：`data.ico.org/globe/api/v1/globe/icip`（主，宽表 `daily[]`）/ `/icip/history`（备，列式）。**无公开 CSV/Excel**——官方明文「on request from stats@ico.org」，旧站历史页 404，`data/.../snapshots/icip.json` 匿名 403
- 匿名窗口 `openFrom=2026-01-01`（载荷 entitlement 字段），实测 2026-01-02→2026-11-05 共 217 交易日 × 5 指标 = 1,085 行；1989 年起的深历史在订阅墙内，**不伪造更早历史**
- 当月值日内修订（月度 PDF 明注），golden 只锚窗口起点 2026-01-02（I-CIP=297.71）
- 周期日度、单端点、无鉴权 → 接入成本低；行模型宽表转长表（date, indicator, price, unit）
- **接入口径偏离（2026-11-07 落档）**：实际单元走**月度 PDF**（当月活文档 + 近 14 个归档月），
  而不是 JSON 门户端点——理由是匿名 JSON 窗口 `openFrom=2026-01-01` 只有 217 交易日，
  而 PDF 归档能把可采窗口推深到 2025-09（实测 1,425 行 / 5 指标）。JSON 端点留作备选通道，未接。

### 路 2 NRA 餐馆业绩指数 RPI（`restaurant-rpi`）
- 工单 lead 已 404；现行官方页 = `restaurant.org/research-and-media/research/restaurant-economic-insights/restaurant-performance-index/`（旧 `economists-notebook/` 路径同字节存活）
- 结构化数据只在月度 PDF 第 3 页表：`/NRA/media/Research/RPI/2024/RPI-<Month>-<Year>.pdf`（目录段恒为 `2024`，非年份），实测 `RPI-December-2025.pdf` 200 / `RPI-January-2020.pdf` 404
- **只有最近 5 个月滚动窗**（Sep-2026 版 = 2026-05→2026-09 × 11 序列），无 2007 以来全史；不做猜 URL 的回补（无归档索引页）
- PDF 文本切块须坐标重建表格（`100.7` 拆成 `100.`+`7`）；同名序列按「Current Situation / Expectations」分节落位 `cs_*`/`exp_*`；中性 100（非旧版 1995=100）
- golden 会随版本老化（锚月约 5 版后滑出窗），replay 失败属预期，重录即可
- 交叉核对：2026-09 rpi / current / expectations 均 =100.7，与官方页正文一致

### 路 3 SAMR 食品安全抽检公告（`samr-food-inspection`）
- 入口是博达 jPaas 壳页 `samr.gov.cn/zw/zfxxgk/fdzdgknr/spcjs/`，数据走 `api-gateway/jpaas-publish-server/front/page/build/unit`（JSON 片段）；**分页必须放 `paramJson`**（URL 直传 `pageNo` 实测仍返第 1 页）
- 历史：列表 `count=228`，末页最早 2019-02-22；pageSize 实测封顶 ~100
- 工单 lead `hd/zjdc/` 是「征集调查」栏目（内容不符）；`tssps/` 同款 JS 壳（特殊食品抽检另在此，未接）；候选主机 `samsu/cjpv/so.samr.gov.cn` DNS 超时——**「抽检公布查询页」不可作公网采集面**
- 栏目构成（99 条实测）：不合格批次通报 64 + 方法公告 14 + 其他 21 → `qualified` 是防御性档，栏目内无实例
- 周期不规则（2026-01~10 共 16 条，月 1–3 条突发成批），轮询取 weekly
- 字段级口径已定义（任务 2.4）：`result_category`（标题规则优先、正文兜底）+ `restaurant_related` 命中规则，6/6 人工判定一致

### 本专场接入状态（2026-11-07 波1 收口：三源全部已接入并点亮）

| 源 | 试跑 | 点亮 cron | 观测 | 口径守卫 |
|---|---|---|---|---|
| `ico-coffee-price` | success 285 行（2025-09-01→2026-11-05 交易日） | `"23 6 * * *"` | 5 条概念 × 285 期入库（us_cents_lb，WORLD） | golden replay ok（按真实宽表形态重锚）；列交叉校验去掉「Colombian 必最高」的行情假设 |
| `restaurant-rpi` | success 5 行（2026-05→2026-09） | `"41 5 2 * *"` | 暂不入库（5 期 < 12 期门槛，跑次留 SKIP 说明，攒够即自动放行） | golden replay ok |
| `samr-food-inspection` | success 100 行（2022-01-07→2026-10-12） | `"27 6 * * 3"` | 事件面不写数值序列（消费方=波4 事件预警 + 波3 读时统计） | golden replay ok；100 条实测 unqualified=65/other=35，餐饮相关 45 |

### 本专场挂账
- 美国餐饮单项序列（Census MRTS `722`）：现只取 `44X72`（零售+餐饮总计），单项待扩 category 列表
- **台股月营收（2026-11-08 更正：此前结论是错的）**：`openapi.twse.com.tw/v1/opendata/t187ap05_L`（上市公司每月營業收入彙總，免 key）**实测 200 / 607KB / 1088 家**，直接取到王品 `2727` 2026-09 月营收 2,090,458 千元、同比 +19.73%。此前记的「`openapi.twse.com.tw` 连接级超时」测的是另外两个端点：`/v1/exchangeReport/STOCK_DAY_AVG/2727` 返 302、`www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?...` 12s 超时；`mops.twse.com.tw` 仍被 FOR SECURITY REASONS 拦（该路确实不通，无需再立项）。**车道性质 = 快照式**：端点只透当期（上一个月）营收、无历史回溯，观测只能按月正向累积。另：原挂账把王品代码写成 `2742`，正码 `2727`
- ICO 深历史（1989 起）与 RPI 全史均需凭据/归档索引，非本波范围

---

# 农业行业专场（2026-11-08，explore → 侦察波 12 路并行已完成）

> **边界声明（必读）**：2026-11-08 已完成 12 路并行端点级侦察，逐路报告原文在 `data-source-scouting/agriculture/<slug>.md`。本节为判读汇总，**冲突以路报告为准**。仍标「未验证」的项（NBS 指标 code、OECD-FAO dataflow id、品种审定字段级、农机月度）是真实未验证，不得当已确认使用。

## 口径与边界（已拍板）

- **行业口径**：申万一级「农林牧渔」（种植/养殖/饲料/动保/种业/渔业/林业/农产品加工）。上游农资（化肥/农药/种子生产/农机）只作成本链变量，**不做公司财务监控**。
- **价格红线**：沿用 2026-10-13 已立切法——**官方统计监测口径可接**（发改委价格监测、农业农村部周报、NBS 流通领域价格、FAO/WFP 官方粮价指数），**商业聚合商现货报价不可接**（生意社/搜猪网/SCFI 类）。
- **财报车道**：A 股走 cn-report（见上方 2026-11-08 决策记录）；港美仅事件面。

## 既有覆盖（实读，非估算）

在产（6）：`fao-food-price`、`fao-empres`、`amis-market`、`usda-psd`、`usda-quickstats`、`un-comtrade`；另有 `moa-hog-price`（国内唯一在产农业官方源）、`ico-coffee-price`（餐饮线顺带）。
停放在册（3）：`wfp-food-price`、`agri-info`、`flower-auction`。
**观测层几乎为零**：全仓 136 单元中注册到观测层的农业概念仅 3 个（`agriculture.supply_demand` / `.supply_demand_balance` / `.crop_area`）。
**cn-report 农业专属规则 = 0 条**（llm_rules 3389 条：`null` 2870 / `*` 481 / `bank` 26 / `insurance` 11 / `securities` 1 / `agriculture` 0）。

## 侦察波结果（2026-11-08 实弹，12 路并行）

> 每路报告原文在 `data-source-scouting/agriculture/<slug>.md`（12 份，995 行）。本节为判读汇总；报告 > 本节（有冲突以路报告为准）。

### 判读总表

| 源 | 判定 | 关键事实 |
|---|---|---|
| MOA 生猪产能 | ✅ 可接入（**季频**） | `moa.gov.cn/ztzl/szcpxx/jdsj/YYYY/YYYYMM/`，静态 `table.data_table`；2026Q3末 能繁母猪 3602 万头（调控目标 96.0%，环比 −4.7%，同比 −10.7%）、生猪存栏 42533 万头。**季更（1/4/7/10 月 20 日）**，月度产能站点不发布 |
| MOA 供需形势 CASDE | ✅ 可接入（月频，HTML 表） | 真通道**不在 moa.gov.cn，在 `www.agri.cn/sj/gxxs/`**；5 张表（玉米/大豆/棉花/食用植物油/食糖）× 18–24 行，含面积/产量/进口/消费/期末库存/价格区间；月更 9–12 日发布；回溯 ≥ No.27（2018-09）；`CASDE-No.` 是稳定期次主键 |
| NDRC 猪粮比价 | ❌ **不可得** | `/fgsj/` 零生猪链接；唯一周度价格栏目数据在 PNG（且来源标为粮食和物资储备局）；`jgjc.ndrc.gov.cn` 已成登录制预警系统；站内检索 404/空。**原定的一级阈值锚落空** |
| 饲料工业协会 | ⚠️ 需 OCR | 月更无会员限制，但核心表是 JPG（`<table>`=0）；正文可提总量、分项只在图里。2026-09：总 3205 / 配合 2996 / 浓缩 119 / 预混 68 万吨 |
| NBS 农业序列 | ⚠️ 本机不可验证 | `data.stats.gov.cn` 全站 WAF 403 `UrlACL`（IPv6/强制 IPv4/QueryData/getTree 全 403）；既有单元形态已知（`zbcode` 扩展零改解析器）；年鉴表全 JPG。**农业只有年度，无月度**；须在生产环境跑 `getTree` 补 code |
| 海关农产品贸易 | ❌ 不可得 | 三主机全前置加速乐（JSL）：412 / 503 / 504，换路径无效；既有单元早已记录同面墙 |
| 渔业 | ✅ 可接入（月累计+年） | `yyj.moa.gov.cn` 正文内嵌表：1–9 月水产品产量 5389.68 万吨（+4.27%）；年度公报 7652.14 万吨 |
| 林业 | ⚠️ 仅年鉴/PDF | 站点 200 但无统计栏目；「统计年鉴」入口是 SPA 空壳 |
| USDA WASDE | ✅ 可接入（月频表格文件） | `.xls` / `.txt` / `.xml` 直链，期号 `wasde{MM}{YY}`；最新 WASDE-676（2026-10）。**坑：未发布期返回 200 + apology HTML，必须校验 content-type 与大小** |
| OECD-FAO Outlook | ⚠️ 未验证 | `oecd.org` / `agri-outlook.org` 三入口全 403（WAF）；`sdmx.oecd.org` dataflow 列表 200（5.9MB）但未命中 AGROUT，须再挖 |
| WFP 市场粮价 | ⚠️ 需重写适配 | 旧库冻结于 **2021-08**；活跃库是 `global-wfp-food-prices`（`last_modified` 2026-11-05，最新观测 2026-10-15，月频，40 个按年 CSV / 620MB），**schema 完全不同** |
| 化肥 | ✅ 可接入（**商业门户**） | `www.fert.cn/10005/` 月度进出口正文含数值（2026-08 尿素出口 52.46 万吨 / 2.18 亿美元 / 416 美元·吨⁻¹）；**产量与出厂价在 vip 需会员**；中肥网是商业门户 → `authority=industry`，不是 association |
| 农药 | ❌ 协会侧不可得 | CCPIA 全站无统计/数据/价格栏目；ICAMA 只有登记许可查询 |
| 农机 | ✅ 年度可接入 | `njhs.moa.gov.cn/nyjxhqk/` 农业机械化发展统计公报（HTML）：2025 作业面积 79.76 亿亩次、综合机械化率 76.82%、拖拉机 1999.19 万台；可见 2022–2025 四期。**无月度官方产销** |
| 品种审定 | ✅ 事件面可接入 | `zys.moa.gov.cn/gsgg/` 同日连发多条省级公示，无时间序列；字段级（是否含品种名/审定编号）未验证 |
| 棉花 | ✅ 可接入（双月） | **`https` 未部署（443 RST），但 `http://www.chinacotton.org/` 200**；`articleList.aspx?sort=1/2/4/5/6`，双月市场监测报告（如 articleID=409 = 2025 年 7–8 月） |
| 糖业协会 | ❌ 不可达（站点侧缺陷） | TLS 走完但证书是 `CN=5-8lab.com`（vhost 错配）→ `curl (60)`；`-k` 后仍 403（nginx）。**代理恢复也救不了**，须换源 |

### 三条推翻原方案的事实

1. **猪粮比价拿不到**（原定一级阈值锚）。但 **能繁母猪存栏 vs 正常保有量可得且是官方口径**（MOA 季报，页面自带「调控目标 96.0%」），阈值层改以它为主判据；猪粮比价降为「不可得留痕」，可选「自算近似（猪价÷玉米价，标注非官方）」。
2. **饲料产量需 OCR**，而用户 2026-10-13 已裁决「扫描件/表格 OCR 类源暂不处理」→ 该源停在留痕，等用户重开裁决，不擅自上 OCR。
3. **海关走不通**（JSL）→ 农产品贸易改走 `un-comtrade`（既有单元）；NBS 农业序列本机 WAF 403 但**生产 tencent 站正常**（既有 manifest 已记），须在生产环境补测 code 后再动 manifest。

### W1 落地结果（2026-11-08 apply，实测逐源留痕）

| 单元 | 动作 | 实证 |
|---|---|---|
| `agri-casde` | 新建 | `www.agri.cn/sj/gxxs/` 五表逐期解析；golden 锚 No.119/2026-05，`replay_sample` `ok=True rows=2000` |
| `moa-fishery` | 新建 | 月累计 + 年度两种粒度分列；golden 窗口钉 2025 全年，`ok=True rows=45`（5389.68 / 7652.14 / 6325.62 万吨） |
| `moa-machinery` | 新建 | 年度公报 2022–2025；golden `ok=True rows=76`（79.76 亿亩次 / 76.82% / 1999.19 万台） |
| `moa-hog-price` | 原位扩展 | 新增 `run_moa_hog_capacity`（季频）；两条 golden 均绿（价格 36 行 / 产能 40 行）；**实测非季末月页无存栏行**，产能只认 03/06/09/12 |
| `usda-wasde` | 新建 | `.txt` 定宽解析；道歉页三重判定实测生效（`wasde1126.txt` = 200 + 369B `text/html` → 判「未发布」不解析）；golden 窗口 2026-10，`ok=True rows=480` |
| `cncotton` | 新建 | **必须 `http://`**（443 RST）；PDF 走 `fd_industry_data.pdftext` 文本层、**不 OCR**；golden 锚 2025-08 十项，`ok=True rows=10`。站点最后一期 = 2025-08，如实声明停更 |
| `fert-cn` | 新建（口径降级） | `authority: industry`（中肥网是商业门户，**未标 association**）；VIP 产量/出厂价不接；golden 锚 2026-08 尿素出口 52.46 万吨 / 2.18 亿美元 / 415.28 美元·吨⁻¹，`ok=True rows=24` |
| `moa-variety-approval` | 新建（事件面） | `zys.moa.gov.cn/gsgg/` 详情页 **`<table>`=0**、品种清单全在 `.doc` 附件（`zxfile/reader` 代理）→ **只登记事件、零数值观测**；golden 锚 2026-11 六条，`ok=True rows=6` |
| `wfp-food-price` | 适配重写 | 迁到 `global-wfp-food-prices`（`last_modified` 2026-11-05）；40 个按年分片，只取当年+上一年；列映射整表重写；golden 锚 2026-10，`ok=True rows=5763 / 16 国` |
| `nbs-stats` | **未动（阻塞）** | 本机全站 403 `UrlACL`，农业指标 code 须在生产环境取；**不臆造 code** |

### W2 落地结果（2026-11-08 写库 + 过门，实测逐条留痕）

写库脚本 `fd-industry-data/scripts/extract_agriculture_wave1.py`（additive，自然键 `uq_sem_obs` 去重，概念先落 `verified=false`），
命名门 `fd-industry-data/scripts/naming_gate_agriculture.py`；序列清单见 `fd-industry-data/docs/agriculture-series-curation.md`。

| 单元 | `source_used` | 观测行 | 概念 | 实测窗口 |
|---|---|---:|---:|---|
| `agri-casde` | `agri-casde` | 500 | 20 | 2024-05 → 2026-10（每序列 25 期） |
| `cncotton` | `cncotton` | 88 | 3 | production 36 / ending_stocks 34 / cotlook 18 |
| `moa-fishery` | `moa-fishery` | 90 | 5 | 18 个月（月累计，2024-07 → 2026-09） |
| `moa-hog-price` | `moa-hog-price` | 133 | 3 + 复用 3 | 产能 20/20/15 季（2021Q4 → 2026Q3）+ 周价各 26 周 |
| **合计** | | **811** | **31** | 其中 9 条 `short_window` 声明 |

- 幂等：重跑同一单元 `inserted=0`（三次实测）。
- 命名门：31/31 `verified=true`；registry `upsert new=31` + `set_verified 31/31`、`demoted=0`；before-snapshot 在 `output/supply-funnel/`。
- 短窗声明与库内期数**逐条相等**（门内硬校验，不符即拒发）：渔业 5×18、cotlook 18、能繁母猪 20、生猪 20、能繁vs目标 15。
- 写库当场抓到的两处真缺陷：① 食糖表与其余四表不同构（无期末库存行 + 行标签改名两次）→ 初版对称映射让 sugar 四条全空/被趋势门丢弃；② 产能抽取器「某季页面超时」仍算成功、留下看不见的序列洞 → 加 `_quarter_gaps` 逐季留痕，不补齐。
- 未注册（有据）：农机 3（4 期）、WASDE 6（2 期）、化肥 3（3 期）、WFP（单国十余期）、渔业年度 5 期 —— 全部 <12 期，只作看板快照。

### W1 留痕（不可得 / 未验证 / 待裁决）

> 每条写两段：**障碍**（实测证据）+ **解锁条件**（什么变了就可以接）。留痕不等于判死，解锁条件成立即重启。

#### 留痕 ① NDRC 猪粮比价 —— ❌ 不可得（原一级阈值锚落空）

- **障碍**：`ndrc.gov.cn/fgsj/` 无任何生猪链接；唯一周度价格栏目数值在 **PNG** 里（且来源标注为粮食和物资储备局）；`jgjc.ndrc.gov.cn` 已成**登录制预警系统**；站内检索 404/空。
- **解锁条件**：① 出现公开 HTML/JSON 的猪粮比价周报栏目；或 ② 用户提供 `jgjc` 账号（登录制，走凭据链）；或 ③ 接受「自算近似 = 生猪均价 ÷ 玉米均价」并显式标注**非官方发布值**。
- **已落地的替代**：阈值主判据改 **能繁母猪存栏 vs 正常保有量**（MOA 季报，页面自带「调控目标 96.0%」）。

#### 留痕 ② 海关农产品贸易 —— ❌ 不可得（加速乐 JSL）

- **障碍**：`stats.customs.gov.cn` / `customs.gov.cn` 三主机全前置加速乐：**412 / 503 / 504**，换路径无效（既有单元早已记录同一面墙）。
- **解锁条件**：官方开放查询接口或数据下载目录；**不自行做 JS 挑战绕过**（涉绕过风控，须用户明确授权另行立项）。
- **已落地的替代**：农产品贸易走 `un-comtrade`（既有单元，HS 章级）。

#### 留痕 ③ 林业 —— ⚠️ 仅年鉴/PDF，无统计栏目

- **障碍**：`forestry.gov.cn` 站点 200 但**无统计栏目**；「统计年鉴」入口是 **SPA 空壳**（39KB，无结构化数据）。
- **解锁条件**：年鉴出 HTML/Excel 下载页，或国家林草局统计公报转为可解析正文。当前不建单元，不占验收门槛。

#### 留痕 ④ 糖业协会 —— ❌ 不可达（站点侧缺陷，非网络问题）

- **障碍**：TLS 走完但证书是 **`CN=5-8lab.com`**（vhost 错配）→ `curl (60)`；`-k` 跳过校验后仍 **403**（nginx）。**代理恢复也救不了**——是站点自身配错。
- **解锁条件**：站点证书/vhost 修复；或换源——统计局/农业农村部食糖料口径、`zce` 白糖期货（既有单元）。
- **旁证**：CASDE 食糖平衡表已覆盖供给需求面，缺口主要在现货价。

#### 留痕 ⑤ 农药 —— ❌ 协会侧无数据栏目

- **障碍**：CCPIA 全站**无统计/数据/价格栏目**；ICAMA `chinapesticide.org.cn/zwb/dataCenter` 只有**登记许可查询**（产品/企业名单，无产量销量价格）。
- **解锁条件**：CCPIA 出月度统计发布；或改走海关 HS 3808 章（当前被 JSL 挡住，见留痕 ②）。

#### 留痕 ⑥ OECD-FAO Outlook —— ⚠️ 未验证（dataflow id 未拿到）

- **障碍**：`oecd.org` / `agri-outlook.org` 三入口全 **403**（WAF）；`sdmx.oecd.org` dataflow 列表 200（5.9MB）但**未命中 AGROUT**。
- **解锁条件**：拿到确切 **dataflow id**（不猜）；或 OECD 恢复公开数据门户；或 FAO 侧 FAOSTAT 供给利用账户替代（`amis-market` 已在产，部分覆盖）。

#### 待裁决 ⑦ 饲料工业协会月度产量 —— ⚠️ 需 OCR（**等用户裁决**）

- **数据面**：月更、**无会员限制**；2026-09 实测总 3205 / 配合 2996 / 浓缩 119 / 预混 68 万吨。正文可提**总量**，分项只在图里。
- **冲突点**：核心表是 **JPG**（详情页 `<table>`=0），要拿到分项必须 OCR；而用户 **2026-10-13 已裁决「扫描件/表格 OCR 类源暂不处理」**。本波**不擅自上 OCR**。
- **解锁条件**：用户重开 OCR 裁决后，按「NFRA 三件套」办（① 新依赖审批 ② 识别结果人工抽检 ③ 失败即红不静默返空）。
- **当前可做而未做**：只提「总产量」单列（正文有数、不需 OCR）——若用户只关心总量，可不破 OCR 裁决先接总量一行。**此选项待用户拍板**。

---

# 花卉专场 Wave（2026-11-08 实测，`add-flower-vertical` 依据）

> 用户 2026-11-08 立项。**决策记录：花卉独立成线**，不与同日立项的农业线（申万农林牧渔）合并。理由：农业线口径=申万农林牧渔且源清单内无任何花卉专属源、其宇宙为申万农业上市公司；花卉的价格链（斗南日价）、贸易链（HS 06 章）、企业面（FLWS / 1377.T）与粮猪饲料不同构。共用层（观测契约/看板门/爬虫自愈/宇宙注册表）按现成契约消费，不重复建设。
>
> **环境事实更正**：本机 `scutil --proxy` 显示 HTTPEnable=0 / HTTPSEnable=0，**无系统代理**；本文档前文记录的 `127.0.0.1:7890` 经实测全部返回 000（已失效）。海外站点**直连可达**，本轮一律 `--noproxy '*'`。检索引擎：DuckDuckGo HTML（0 字节）与 Bing（~250 字节）均被拦截，**百度可正常返回**（~1MB HTML）。
>
> **与农业专场的一致印证**：本轮独立实测得到「海关 412 / 统计局 403 / 改走 `un-comtrade`」，与上方农业专场结论完全一致——两线各自撞同一堵墙，说明这是平台级事实而非个案。

## 中国境内

| 源 | 端点(实测) | 直连 | 形态 | 鉴权 | 周期 | 历史深度 | 反爬 | 样本证据 | 成本 | 价值 |
|---|---|---|---|---|---|---|---|---|---|---|
| **昆明市农业农村局·价格行情** | `nyncj.km.gov.cn/nygz/jgxq/` | ✅200 | 静态 shtml + 表格 | 无 | **日** | **仅滚动 2–3 月**（`index_5`→2026-10-13；`index_20`→404） | 无 | 单篇 1 表 25 行；列=`品名/计量单位/最高价/最低价/均价`；样例「红玫瑰（单头）元/枝 0.35/0.22/0.27」「绣球 元/枝 10.32/7.17/8.31」；来源标注「昆明斗南国际花卉产业园开发有限公司」；详情页 `/c/YYYY-MM-DD/<id>.shtml` | S | **高** |
| 国家林草局 | `forestry.gov.cn` | ✅200 | 门户 + API 网关（`jpaas-publish-server`） | 无 | 年/公告 | 待实测 | 无 | 首页 85 KB 正常；API 网关路径 301（形态待 W0 定位） | M | 中高 |
| 农业农村部 | `moa.gov.cn` | ✅200 | 门户 | 无 | 月/公告 | — | 无 | 首页 114 KB 正常 | M | 中 |
| KIFA 昆明花拍 | `kifa.net/{kIFAPriceIndex,breedQuotation,info}.do` | ❌**468** | — | — | 日 | — | **雷池 SafeLine WAF**（`server: Tengine` + `sl-session` cookie + `/.safeline/static/favicon.png`），带完整浏览器头仍 468 | 三端点响应体均 14,863 B 挑战页 | L | 高但不可得 |
| 中国花卉协会 | `chinaflower.org` / `.org.cn` / `chinaflower.org.cn` | ❌000 | — | — | — | — | 域名停放 | `chinaflower.org` DNS→`exp.gname.net`；`.org.cn`→NXDOMAIN；`chinaflower.org.cn`→000 | — | 已死 |
| 云南花卉 | `flowers.yunnan.gov.cn` / `ynflower.gov.cn` | ❌000 | — | — | — | — | — | 均不可达；归档单元 `yunnan-flowers` 的 `spider.py` 含 UCI/FRED 占位 URL（模板垃圾） | — | 已死 |
| 斗南门户 | `dounan.gov.cn`(❌000) / `dounan.cn`(✅200, 4.6 KB gbk) | 混合 | 壳页 | 无 | — | — | — | 后者仅 4.6 KB | — | 低 |
| 花讯网 | `flowercn.net` | ✅200 | Discuz 论坛 | 无 | 日(资讯) | — | 无 | 118 KB，栏目为资讯/社区/栽培，无结构化数据 | — | 低 |
| 中国海关 | `stats.customs.gov.cn` / `customs.gov.cn` | ❌**412** | — | — | 月 | — | Precondition Failed（前置加速乐，需 cookie/JS 握手） | 412 + 2.5 KB | L | 高但绕行（Comtrade 覆盖） |
| 国家统计局 | `data.stats.gov.cn/easyquery.htm` | ❌**403** | — | — | 月 | — | WAF | 403 + 315 B（生产站另有通道，见农业专场） | — | — |
| 全国标准平台 | `std.samr.gov.cn` | ✅（既有 `gb-standards` 单元） | JSON | 无 | 实时 | — | 无 | 复用既有单元 | — | 中 |
| 花卉展会/门户 | `hortiflorexpo.com`(✅200) / `59178.com`(✅200) / `31expo.com`(301) / `cnfxw.com`(114 B) | 混合 | HTML | 无 | 不定期 | — | 无 | 均无结构化数据通道 | — | 低 |
| 云南/园林类 | `ynyhxh.com`(429) / `ynflower.org`(404) / `yuanlin.com`(000) / `hm160.cn`(000) | 混合 | — | — | — | — | 429 限流 | — | — | 低 |

## 全球

| 源 | 端点(实测) | 直连 | 形态 | 鉴权 | 周期 | 历史深度 | 样本证据 | 成本 | 价值 |
|---|---|---|---|---|---|---|---|---|---|
| **UN Comtrade** | `comtradeapi.un.org/public/v1/preview/C/A/HS` | ✅200 | JSON | 无 | 月/年 | 1962 起 | `reporterCode=156&period=2023&cmdCode=0601,0602,0603&flowCode=X` → **204 行**；字段含 reporterCode/partnerCode/cmdCode/period/flowCode/classificationCode=H6；实测 cmdCodes=`0601/0602/0603` | **零新建**（`un-comtrade` 既有参数化） | **高** |
| **Eurostat** | `ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apro_cpsh1` | ✅200 | JSON | 无 | 年 | 多年 | `geo=DE&time=2023` → 19,672 B 正常 | **零新建**（`eurostat-api`） | 高 |
| AIPH 国际园艺生产者协会 | `aiph.org` | ✅200（301→aiph.org） | HTML | 无 | 年 | — | 首页 88 KB 正常；年鉴（International Statistics Flowers and Plants）可及性待 W0 实测 | S–M | 中高 |
| Expoflores（厄瓜多尔） | `expoflores.com` | ✅200 | HTML | 无 | 月/年 | — | 首页 1.0 MB 正常 | M | 中高 |
| Kenya Flower Council | `kenyaflowercouncil.org` | ✅200 | HTML | 无 | 年/月 | — | 首页 109 KB 正常 | S–M | 中 |
| Union Fleurs（欧洲花卉贸易） | `unionfleurs.org` | ✅200 | HTML | 无 | 年 | — | 首页 169 KB 正常 | S | 中 |
| USDA NASS | `quickstats.nass.usda.gov/api` | ✅有响应（DEMO key 401） | JSON | 免费 key | 年/周 | 多年 | 401 + 26 B（key 无效，端点可达）；花卉口径走 HORTICULTURE 商品参数 | **零新建**（`usda-quickstats`） | 中高 |
| 日本 e-Stat | `e-stat.go.jp` | ✅（既有单元） | JSON | appId | 月/年 | 多年 | 花き 走 `search_word` 参数 | **零新建**（`jp-estat`） | 中高 |
| 日本 MAFF 花き | `maff.go.jp/j/tokei/kouhyou/kaki/` | ❌**403** | — | — | 年 | — | 403 + 37 KB（bot 拦截） | — | 绕行 e-Stat |
| **Royal FloraHolland** | `royalfloraholland.com` | ❌**403** | — | — | 日 | — | Cloudflare 403 + 386 B；核心数据在付费 Connect | — | 不可得 |
| USDA 门户 | `usda.gov` | ❌**403** | — | — | — | — | 403 + 366 B（bot 拦截） | — | 绕行 API |
| 荷兰 CBS StatLine | `opendata.cbs.nl/ODataCatalog/Tables` | ✅200 | OData JSON | 无 | 年 | 旧表 | 5,980 张表全量拉取后本地筛 `bloem/sierteelt/plant/boomkweker`：当代花卉产量**无表**，仅 1996–2013 旧表（`60042ned`/`80110ned`/`80125ned`/`81643NED`） | — | 低（放弃） |
| 哥伦比亚 Asocolflores | `asocolflores.org` | ❌000 | — | — | — | — | 不可达 | — | 不可得 |

**已死/不可用清单**：`chinaflower.org`（域名停放）、`chinaflower.org.cn`（NXDOMAIN）、`cnflowers.org.cn`（NXDOMAIN）、`flowers.yunnan.gov.cn`、`ynflower.gov.cn`、`dounan.gov.cn`、`xinhua08.com` / `index.xinhua08.com`（新华指数旧域）、`asocolflores.org`、`yuanlin.com`、`hm160.cn`、`cnfxw.com`（壳页）。**被 WAF/反爬阻断**：`kifa.net`（雷池 468）、`stats.customs.gov.cn` + `customs.gov.cn`（412）、`data.stats.gov.cn`（403）、`maff.go.jp` + `usda.gov`（403）、`royalfloraholland.com`（403 Cloudflare）、`ynyhxh.com`（429）。

## 企业面（实测证伪，非估算）

| 候选 | 市场 | 实测结论 | 依据 |
|---|---|---|---|
| **FLWS** 1-800-FLOWERS.COM | 美股 NASDAQ | ✅**纯花卉零售，纳入纯花卉层** | CIK `1084869`；`company_tickers.json` 命中 |
| **1377.T** Sakata Seed | 日股 TSE | ✅种苗育种，纳入纯花卉层 | EDINET 无 key 返回错误画面（需免费 key） |
| 花王股份 `603007` | A股 | ❌**排除**：主营已变 | 东财 F10 主营构成 2026H1：新能源混动汽车核心零部件 **98.24%**、工程 1.70% |
| 云投生态 `002200` | A股 | ❌**不纳入纯花卉层**：苗木占比合计仅 0.23% | 2026H1：工程施工 **97.70%**、苗木销售 0.15%、苗木租摆 0.08% |
| 丰乐种业 `000713` | A股 | ⚠️邻接（种业，非花卉专属） | 2026H1：农化 69.65%、种子 16.51%、香料 13.85%，无花卉分部 |
| `FLO` Flowers Foods | 美股 | ❌**名字陷阱**：烘焙公司 | SEC title = FLOWERS FOODS INC（烘焙） |
| `AFCG` Advanced Flower Capital | 美股 | ❌**名字陷阱**：大麻贷款 REIT | SEC title 命中但业务为大麻金融 |
| `GSIW` Garden Stage | 美股 | ❌**名字陷阱**：港资资产管理 | SEC title 命中但非园艺 |
| 邻接候选 | 美股 | ✅纳入邻接层 | `CENT`（Central Garden & Pet）、`SMG`（Scotts Miracle-Gro）、`HYFM`（Hydrofarm）、`EDBL`（Edible Garden） |
| 港股 | HK | ❌**无纯花卉标的** | `hkexnews` `titleSearchServlet` 搜 `flower`，2026-01-01→2026-11-08，`recordCnt=0` / `result="[]"` |
| 欧股 | EU | ❌**无上市标的** | FloraHolland / Dutch Flower Group / Dümmen Orange / Ball Horticultural 均为合作社或私有 |
| 新三板 | 中国 | ⚠️未确认 | `neeq.com.cn` 查询端点持续 302；`cninfo` `column=neeq` 返 0。不作为依据，W0 可选复核 |

## 财务细分实测（关键约束）

| 项 | 实测 | 含义 |
|---|---|---|
| SEC `companyfacts`（FLWS） | 398 个 us-gaap 概念；`BloomNet`/`Gourmet`/`Consumer Floral` 出现次数**均为 0**；有 `NumberOfReportableSegments` 但无维度分解 | **聚合接口剥掉分部维度**，不能作为分部来源 |
| SEC 10-K instance（`0001084869-26-000029` / `flws-20260628_htm.xml`，1.75 MB） | `explicitMember` **412 个**；`us-gaap:StatementBusinessSegmentsAxis` **57** 个 context；可抽 **60 条**分部收入事实 | **分部在 instance 里**，可解析 |
| 成员命名 | 真实成员 `flws:ConsumerFloralAndGiftsMember`、`flws:GourmetFoodsAndGiftBasketsMember`、`flws:BloomNetMember`；`ConsumerFloralMember` 计数 **0** | 成员为**公司自定义命名空间**，须逐家人工映射，**禁止名称匹配** |
| 事实重复 | 同一数值在多个 context 重复出现 | 必须按（概念, context, 单位, 精度）去重，否则合计翻倍 |
| 东财 F10 主营构成 | A股 `002200`/`603007`/`000713` 均返 12 行含 `MAIN_BUSINESS_INCOME`/`MBI_RATIO`/`GROSS_RPOFIT_RATIO`；`FLWS.N`/`1377.T`/`833547.BJ` 均 **0 行** | **A股分部零新建**（既有 `stock-zygc` 单元）；美股/日股不覆盖 |
| SEC 花卉/园艺关键词全量比对 | `company_tickers.json`（796 KB）筛 FLOWER/HORTICULT/SEED/GARDEN：命中 FLWS / FLO / AFCG / GSIW / CENT / EDBL / COOT / SMG / HYFM | 关键词召回率高但**假阳性率高**，必须逐家核主营 |

## Top 5 排序（能真正支撑三板）

1. **昆明市农业农村局·斗南日价** —— 唯一可得的花卉日频价格官方面，价格与供给板的骨架。代价是滚动窗 2–3 月，走即接即累积。
2. **UN Comtrade HS 0601/0602/0603** —— 全球贸易链板的骨架，零新建。
3. **Eurostat `apro_cpsh1`** —— EU 花卉园艺产量，零新建，补贸易链的供给侧。
4. **SEC instance 维度抽取** —— 唯一能回答「财务细分」的通道（聚合接口已实测不可用）。
5. **AIPH + Expoflores + Kenya FC + Union Fleurs** —— 全球供给面的半定量补充，四站点均可达，需 3–4 个新单元。

### 花卉 W0 端点级复测（2026-11-08 01:00–01:30 UTC+8）

上一节把 AIPH / Expoflores / Kenya FC / Union Fleurs 记成「四站点均可达，需 3–4 个新单元」。
**端点级复测后这个结论必须改写：四源里只有 AIPH 有结构化数据，其余三源没有可接序列。**

| 源 | HTTP | 结构化产物 | 判定 |
|---|---|---|---|
| **AIPH** `aiph.org` | 200（首页 78 KB；年鉴索引 248 KB/267 KB body；年版页 196 KB） | **公开 XLSX 三件**，含「分品种章节本」27 个工作表 | **可接**（已落 `spiders/aiph-stats`） |
| Union Fleurs `unionfleurs.org` | 200（168 KB） | **无自有统计**；站内仅新闻，唯一统计信息是「AIPH 与 Union Fleurs 联合出版年鉴」 | **不建单元**（同名数据从 AIPH 取，避免双计） |
| Kenya Flower Council `kenyaflowercouncil.org` | 200（109 KB） | 只有 `KFC_FSA_Report_2024_Full_Web_Version.pdf` 等可持续性/认证 PDF；无面积/产量/出口时间序列 | **降级留痕**（肯尼亚出口量走 Comtrade HS0603，比协会口径更干净） |
| Expoflores `expoflores.com` | 200（1.0 MB，Wix/JS 站） | 「Biblioteca Digital」为 Wix 动态页（`/biblioteca-digital` 实测 **404**，链接由 JS 渲染），无 CSV/XLSX | **降级留痕**（厄瓜多尔出口走 Comtrade/BCE） |
| 国家林草局 `nfga.gov.cn` | **000（域名已废）**；实际站在 `forestry.gov.cn` | 见下 | **降级留痕** |

**AIPH 是本线第二个大发现（仅次于斗南）**：`https://aiph.org/giic/international-statistical-yearbook/`
列出各年版数据页 `<年>-yearbook-data-links/`（2022–2025 均在线），年版页公开 XLSX 直链：

| 年鉴年 | 分品种章节本文件名 |
|---|---|
| 2025 | `ISYB_2025_production.xlsx`（135 816 B，27 表） |
| 2024 | `SYB_2024_chapter2_products-_pages.xlsx`（136 164 B，27 表） |
| 2023 | `SYB_2023_chapter2_products-_pages.xlsx` |

- 章节本 27 表 = 9 品种 × (`Trade` / `Graph` / `Production|area`)；9 个面积表：
  Rose / Carnation / Orchid / Chrysanthemum / Lily / Christmas trees / Cut Foliage /
  Flowering plants / Green and Foliage plants。
- **面积是真正的空白**：EU 外（印度/中国/厄瓜多尔/哥伦比亚/肯尼亚/墨西哥/越南/泰国）的花卉分品种
  种植面积别处拿不到。Trade 表脚注写明 `Source: Euroststat, provisional data 2024` +
  `Data based on table 3.2. Roses, Imports (CN-Code 06031100)` ⇒ 是 Eurostat 二次发布，
  既有 `eurostat-api`/`un-comtrade` 已覆盖，**重复接入会双计**，故单元只做面积。
- **每行自带参考年**：2025 版玫瑰花面积 India 2023 / China 2020 / Ecuador 2024 / Colombia 2024 /
  **Kenya 2012** / Italy 2005 ⇒ 跨截面＋古董年份混装，不是时间序列。
- **操作坑（硬）**：CDN 中途截断——同一 URL 三次下载落 119679 / 131982 B，而 `content-length`
  恒为 136164；截断包 `BadZipFile`。必须 `Range` 续传补齐 + `testzip()` 验包后才解析。
  该站还会偶发 40–60 s 卡在 9 KB（复现 1 次）。
- 实测全量：**81 行 / 9 表 / 9 品种**（rose 17、chrysanthemum 16、carnation 13、lily 10、
  christmas_tree 8、flowering_plant 5、cut_foliage 4、orchid 4、green_foliage_plant 4），
  `area_ha` 无 None 无 0，脚注剥离命中 7 处（全为 `Netherlands 3`）。
- 上游自身不一致：Orchids `Netherlands 3` Total 80 ha 但 Under protection 90 ha —— **照录不对账**。

**国家林草局（1.3 结论）**：`www.nfga.gov.cn` **000（域名死）**，真实站在 `www.forestry.gov.cn`（200）。
站内检索 API 实测可用（JEECMS）：
`GET /content/searchES?siteId=&...&q=<关键词>&page=1&size=20` → 200 JSON（花卉产业 112 435 命中，
`花卉统计` 12 330）。但：

- 命中项**全是新闻稿**（"中国花卉产业蓬勃绽放"、"我国种苗花卉年产值 5200 多亿元"…），
  没有结构化统计表；`2017全国林业发展统计公报` 的 `txt` 字段 **21 字符空壳**。
- 真正的统计载体是 `中国林业和草原统计年鉴 2024`（contentId **687813**，`channelName=统计年鉴`），
  正文 `txt` 为空，实件是附件 **`/u/cms/www/202609/08143845d8xm.pdf`**（**25 MB / 146 页**）。
  实测该 PDF **一个字体对象都没有**（`/Font` 0、`/Type0` 0、`/TrueType` 0）、18 个 `JPXDecode`
  图像流，`pdftotext` 抽 1/20/60 页**各 0 字符** ⇒ **纯扫描件，无文字层**。
- 判定：**结构化不可接**，降级两段式留痕。解锁条件 = ①OCR 管线（PaddleOCR/云 OCR）入仓，
  或 ②林草局改发 HTML/XLSX 统计表。

### 花卉 W0 企业面复核（1.5，2026-11-08）

- **SEC 关键词全量比对**（`company_tickers.json`，796 KB）：FLOWER / HORTICULT / SEED / GARDEN 召回
  `FLWS`(Flowers Foods… 实为 **1-800-FLOWERS**)、`FLO`(**Flowers Foods 烘焙**，名字陷阱)、
  `AFCG`(**大麻贷款 REIT**，陷阱)、`GSIW`(港资资管，陷阱)、`CENT`(Central Garden & Pet)、
  `EDBL`(Edible Garden)、`COOT`(Australian Oilseeds)、`SMG`(Scotts Miracle-Gro)、`HYFM`(Hydrofarm)。
  ⇒ **纯花卉层闭集 = `FLWS`(CIK 1084869) + `1377.T`(Sakata Seed，日股)**；
  邻接层 = `CENT` / `SMG` / `HYFM` / `EDBL`（园艺投入品与受控环境农业）。
- **`1377.T` 票符未上游核实**：EDINET API key **未申请**（全仓无 key，酒店线同样挂账
  `docs/hotel-universe.yaml` 第 301 行「票符未核实：EDINET API key 未申请」）。
  解锁条件 = 申请 EDINET key 后按 `jp-estat` 同级通道核对有価証券報告書。
- **欧股无纯花卉上市标的**：Royal FloraHolland（荷兰花荷）是**合作社**、Dümmen Orange / Selecta One
  （育种）为**私有**、Ball Horticultural（美）私有。⇒ 双层宇宙里欧洲只出现在**国家维度**
  （AIPH 面积 / Eurostat 产量 / Comtrade 贸易），不出现在公司维度。
- **A股无纯花卉主业标的**（东财 F10 主营构成逐家实测，见上文证伪 4）：`603007` 新能源汽车零部件
  98.24%、`002200` 工程施工 97.70%（苗木合计 0.23%）、`000713` 农化 69.65%。A股只进邻接层，
  且 `flower_revenue_share` 必须按 `stock-zygc` 分部占比如实填（多为 0.1–0.2% 量级）。
- **港股 hkexnews 搜 `flower` 2026 全年 `recordCnt=0`** ⇒ 港股层空集，`universes/hk.yaml` 记空集结论。

# 酒店行业专场（2026-11-08，change `add-hotel-vertical` 波1）

> 详情四份：`data-source-scouting/hotel/{mct-star-hotel,tourism-demand,ctha-report}-scouting.md` + `meadin-verdict.md`

## 三源实测结论（一句话版）

| 源 | 主机 | 形态 | 周期 | 最新 | 判定 |
|---|---|---|---|---|---|
| 文旅部·星级饭店季报 | `zwgk.mct.gov.cn` | 4 张 xlsx/期（哈希名）+ 正文 PNG | 季 | **2024Q3（已停更）** | **接入**，覆盖 2023Q4–2024Q3 |
| 文旅部·国内居民出游数据 | `zwgk.mct.gov.cn` | 纯 HTML prose（无附件） | 季 + 年度公报 | **2026 前三季度** | **接入**（最活跃） |
| 中国饭店协会·年度报告 | `www.chinahotel.org.cn` | PDF（哈希名，InDesign 文本层） | 年 | 2026 版（数至 2025-12-31） | **接入**（结构化最好） |
| 迈点 MBI | `www.meadin.com` | JS Cookie 挑战（全路径同一 8,235 B） | — | — | **放弃·显式不可得** |

> **2026-11-08 复核（7.3 端到端演练顺带做）**：三源全部重测，**均无新期次** ——
> 星级饭店仍停在 2024Q3（停更）；文旅部出游真爬一次（`crawl_runs.id=4923`，rows=64）
> 得 64 行与库内逐条一致，最新仍是 **2026 前三季**；欧盟四条命令真取 745 行、与库内同窗
> （月度夜数至 **2026-08**、营业指数至 **2026-07**）。结论是「上游没发新稿」，不是我们没抓到。

## ★接：文旅部星级饭店季报

- 栏目 `https://zwgk.mct.gov.cn/zfxxgkml/447/465/index_3081.html`（**少一层 `447` 直接 404**）
- 最新 2024Q3（2024-12-26）：4 张 xlsx，13.7–18.2 KB/张，直连 200、无鉴权、无验证码
- 三维度齐全：**分省**（全国+31 省+新疆兵团=33）× **按星级**（一星–五星=5，仅数量/ADR/OCC）×
  **50 重点旅游城市**（51 行，含「全国」= 50 城小计）
- 全国行真值锚点（2024Q3）：`6129 家 / 390.01 亿元 / ADR 375.10 / OCC 52.96% / RevPAR 198.66`
- **最大事实：该系列 2024Q3 后停更**。2024Q4、2025Q1–Q3、2026Q1–Q3 精确检索 `totalHits=0`；
  统计信息栏目 2024-12-26 之后 12 条无星级饭店条目。2025 年只有公报里的全国单点
  （7586 家 / 1448.0 亿 / ADR 360.2 / OCC 46.8%），无附件无分省。
  → 这是任务 6.4/6.5「发布节奏预警」的**天然真样本**（真实停更，不是构造）。
- 坑（13 条见详情档，最毒三条）：① 2024Q1 附件 1/2 名不符实且**逐单元格重复**（都是「统计完成表」，
  不含经营指标）→ 解析器必须校验内页标题；② 50 城表「全国」行是 50 城小计（2209 vs 6129）；
  ③ 空值是**全角「－」**（U+FF0D），不是 `-`、不是空、不等于 0。

## ★接：文旅部国内居民出游数据

- 与星级饭店**同栏目**，按标题前缀区分（`…国内居民出游数据情况` vs `…全国星级旅游饭店统计调查报告`）
- **纯 HTML prose**，数字在中文句子里：`53.07亿`（人次）/ `4.95万亿元`（花费）
- 实测 6 期连续（2024 年度 → 2026 前三季度），每期都给**城镇 / 农村**两档

| 期次 | 出游人次 | 同比 | 花费 | 同比 |
|---|---|---|---|---|
| 2025 前三季度 | 49.98 亿 | +18.0% | 4.85 万亿 | +11.5% |
| 2025 年度 | 65.22 亿 | +16.2% | 6.30 万亿 | +9.5% |
| 2026Q1 | 19.01 亿 | +6.0% | 1.86 万亿 | +2.9% |
| 2026 上半年 | 34.63 亿 | +5.4% | 3.21 万亿 | +2.0% |
| 2026 前三季度 | 53.07 亿 | +6.2% | 4.95 万亿 | +2.2% |

- **累计 + 单季并存**：上半年稿额外给「分季度看，一季度 19.01 亿…二季度 15.62 亿」→
  必须按 `ytd` / `quarterly` 两个粒度建概念，与 A 股锦江「1-11 月 vs 单月」同类陷阱。
- 配套：`2026-06-02` 的 2025 年统计公报一句话给**入境 15450 万人次(+17.1%) / 出境 14836 万(+20.8%) /
  旅行社 70354 家 / 星级饭店 7586 家 / 营收 1448.0 亿 / ADR 360.2 / OCC 46.8%** ——
  这是 5.2 供需板**同年同源的供需交汇点**。

## ★接：中国饭店协会年度报告

- 真站 **`www.chinahotel.org.cn`**（`ctha.com.cn` 实测 `000` 域名死）；PDF 走 `/sfs/cms/<32位hash>.pdf`
- 两份 2026 版（InDesign，`Tagged: yes`，文本层完整）：`hotel2026.pdf` 32 页 / 19.1 MB；
  `group2026.pdf` 53 页 / 12.9 MB
- **行业面（hotel2026）**：住宿业 59.3 万家 / 2051.5 万间；酒店业 37.5 万家 / 1873.6 万间（63%/91%）；
  连锁客房 783 万间 / 非连锁 1090 万间 → **连锁化率 41.80%**；广东 212 万间、北京 50.5 万间。
  目录含 **2016–2025 十年门店数/客房数序列**、按档次/规模/城市级别分组、31 省排序。
- **企业面（group2026）**：**前 50 集团表整表可抽**（锦江 1,368,057 间 / 14,132 店；华住 1,264,419 / 12,858；
  首旅如家 554,919 / 7,802；格林 331,013 / 4,604；东呈 226,915；亚朵 224,423…），
  四档品牌榜同构；概要点给 连锁 10.63 万家 / 783.18 万间(+10.74%)、前 50 共 594 万间(+10.23%)、
  前 10 共 465 万间(+8.71%)、占连锁市场 **59.38%**。
- **与宇宙天然对应**：锦江/华住/首旅/格林/亚朵 同时是 A 股 6 家与美股 GHG/ATAT/HTHT 的实体 →
  这是 5.3 公司板「企业自报口径 vs 协会口径系统规模」的**交叉校验面**。
- 坑：① 图页可能抽不出序列（纯图形无数据标签）→ 逐页判「文字页/表格页/图形页」，图形页不猜值；
  ② 期次是「截至上年 12-31」→ 2026 版 = 2025 年末；③ **集团榜 vs 品牌榜同名不同实体**
  （`锦江国际酒店` 品牌 23,936 间 ≠ `锦江` 集团 1,368,057 间）；④ 协会口径 ≠ 星级饭店口径
  （37.5 万家 vs 6129 家，**两个宇宙不可混算**）。

## 放弃：迈点 MBI（**裁决已推翻重写**）

- 旧记录「502 / 12s 超时」**不成立**：502 是 WAF 拒绝裸 `curl` UA（无 `Accept`/`Accept-Encoding`）。
  补全浏览器头 + HTTP/2 → **200 / 0.28 s**。
- 真实障碍：返回的 8,235 字节是 **JS Cookie 挑战页**（`body onload="check()"` + 隐藏 `parm_0/parm_1` +
  混淆 JS 解 cookie）。**`robots.txt` 与 `sitemap.xml` 也是同一个挑战页** → WAF 拦站点入口，无静态旁路。
- 代理轮**无法测**：系统代理当前关闭（`scutil --proxy` → `HTTPEnable 0`），7892 端口未监听。
- 判定 **放弃·显式不可得**，理由 = `anti-bot-js-challenge`（不是鉴权、不是付费墙、不是超时）。
  等价替代 = 中国饭店协会品牌/集团榜（可引用、可审计）。解锁条件两段式见 `hotel/meadin-verdict.md`。

---

# 花卉全球供给面探针降级（2026-11-10，industry-source-solution-fleet P4）

> 探针：`fd-source-probe`（本机直连，出口 IPv6 2408:8256:…轮换）；10 次探测台账见
> `openspec/changes/archive/2026-11-11-industry-source-solution-fleet/replay/` 与 `fd-source-probe` 审计。
> 结论：**golden §A5「四站点均可达，需 3–4 个新单元」经实测降级**——首页可达 ≠ 有数据通道。

| 站点 | 本轮实测 | 降级结论 |
|---|---|---|
| Expoflores（厄瓜多尔） | 首页 200（Wix 模板站）；`/estadisticas/`、`/exportaciones/`、`/category/estadisticas/` 均 404；sitemap→pages→`/bibliotecadigital` 200 但仍是 Wix 壳 | **无结构化数据通道**，数字图书馆是 PDF 陈列；0 张生成单 |
| Kenya Flower Council | 首页 200（Joomla）；文章页 200 但为新闻/认证内容站；sitemap 无统计路径 | **无统计 API**；0 张生成单 |
| Union Fleurs（欧洲） | 首页 200（WordPress）；`/publications/` 404；`resources-sitemap` 200 全是新闻稿 | **新闻/资源站**，无数据表；0 张生成单 |
| 国家林草局 | 首页 200（静态 XHTML） | 维持既有结论：门户形态，API 网关 301 待 W0 定位 |
| USDA quickstats（花卉口径） | `api_GET?key=DEMO_KEY&commodity_desc=FLORICULTURE` → **401** `{"error":["unauthorized"]}` | 凭据无效（Wave C 既有标注维持）；解锁=统一密钥轨道注册 free key |

**纪律生效记录**：这是「无证据不出单」第一次真实拦下侦察簿的 ★接 判定——4 个 ★接
（花卉全球供给面）全部降级为「首页可达、无数据通道」。落仓前必须先找到结构化端点，
找不到就留在候选清单待测态。

---

# 欠账复测队列 · 第一批（US 官方 5 条，2026-11-10，fd-source-probe 实测）

> 背景：candidates.json 的「已接无落地出处 37 条」是侦察簿 ★接 但从未落仓的真实欠账。
> 本轮对 US 官方 5 条做活性复测（USAspending/data.gov 目录/Treasury FiscalData/Census/OpenSky）。

| 源 | 本轮实测 | 定案 |
|---|---|---|
| USAspending | `GET /api/v2/awards/last_updated` → 200 `{"last_updated":"11/06/2026"}` | **活跃待接**（联邦合同按 NAICS 月度聚合=行业需求信号，W1-L2 原判维持） |
| data.gov 目录 | `GET /organizations?api_key=DEMO_KEY` → 200，255,636 数据集目录（DEMO_KEY 可用；侦察簿所记 `/refs` 路径为误记） | **活跃待接**（只做发现层，W1-E 原判维持） |
| Treasury FiscalData | 侦察簿所记 v1 路径与 v2 全 404（HTML 404 页）；`transparency.treasury.gov` 302 | **⚠ 2026-11-11 已推翻**：见第七批反转记录——v1/v2 三条端点实测 200 且体首 `{"data":[`。原判「端点路径漂移，需重侦察；当前不可出单」**作废**（`transparency.treasury.gov` 的 302 仍成立，那是另一个面，判据各自独立） |
| Census API | `data.json` → 403 Cloudflare 拦截页（HTML，oldie 注释） | **按出口拦截**（非凭据）：换海外出口复测；免费 key 仍须注册（防 HTML 伪装 200，W1-L37 原注记维持） |
| OpenSky | 未探（匿名限流严格） | 维持原判（keep-candidate） |

**口径记录**：这 5 条在 candidates.json 状态均为 accepted（欠账），本轮复测不改变「接不接」
的判定，只更新活性事实——**出单判定仍归生成链**（USAspending/data.gov 出单时按「只做
发现层/聚合信号」的价值口径过定案岗）。

---

# 欠账复测队列 · 第二批（中国/国际 4 条，2026-11-10）

| 源 | 本轮实测 | 定案 |
|---|---|---|
| data.gov.uk CKAN | `package_search?q=flower&rows=2` → 200（CKAN 标准 API 活） | **活跃待接** |
| OpenDataSoft | `/api/explore/v2.1/catalog/datasets?limit=2` → 200（102,992 目录） | **活跃待接** |
| 深圳开放平台 | `datasetCatalog` → 200 但 `errorCode:10009 appKey不能为空` | **需免费 appKey 注册**（Wave E 既有标注维持） |
| 水利部水雨情 | `xxfb.mwr.cn/portal/hydroinfoByDays` 本机直连 ConnectTimeout | **换出口/集群侧复测**（集群有既有浏览器指纹通道先例，见 1.2 nbs 403 注） |

---

# 欠账复测队列 · 第三批（4 条，2026-11-10，fd-source-probe 实测）

> 教训沿用花卉 P4：**首页 200 ≠ 有数据通道**。本批 4 条首页全 200，但只有 1 条真能取数。

| 源 | 本轮实测 | 定案 |
|---|---|---|
| GDACS（RSS+API） | `gdacs.org/xml/rss.xml` → 200 + **RSS 2.0 XML**，200KB 内 `<item>` 65 条，带 `geo:` 命名空间 | **活跃待接**（真结构化通道：XML feed 可直接解析，含经纬度与 alertlevel） |
| 搜猪网生猪大数据 | 首页 200，拉满 25,193 B（未截断）；表格是 `<tbody id="reptable">` **空壳**——内含「数据加载中。。。」占位，唯一 `<tr>` 还被 `<!-- -->` 注释包裹 | **不可静态取数**：数据由 JS 异步填充，静态抓只能拿到壳。需找其 XHR 端点或走浏览器通道（另立侦察） |
| 生意社 100ppi | `100ppi.com/cindex/` → **HTTP 200 但响应体是 JS 挑战页**（`<meta name="robots" content="noindex">` + 混淆 `_0x1/_0x2` 脚本 + 日期 token） | **按 WAF 拦截处理**：200 是伪装，实际要过华为云 WAF 两步 cookie 握手。与侦察簿原注一致，不因 200 判可得 |
| 国家统计局门户 | `stats.gov.cn` 首页 200 | **维持原判**：首页可达但数据在 easyquery 上，而 easyquery 是 403 拦截页（见陷阱清单 `nbs-easyquery-blocked`）。首页 200 不可作为可得证据 |

**方法论收获（进陷阱清单硬要求）**：本批两条（100ppi、搜猪网）都是「HTTP 200 + 非空体」，
探针按 HTTP 层判成 `ok`。这正是 spec `source-probe` 那条「分类边界 + 阳性断言」的现实版：
**对这两类站点，必须给 `expect_contains` 的数据标识（如真实数值行/JSON 字段）才判得出**，
只凭 200 会把 WAF 挑战页和 JS 空壳当成可得。

---

# 欠账复测队列 · 第四批（5 条，2026-11-10，fd-source-probe 实测 + 阳性断言）

> 本批每条都给了**阳性 `expect_contains`**（数据标识），不靠 HTTP 200 判可得——第三批
> 100ppi/搜猪网的教训：200 可能只是 WAF 挑战页或 JS 空壳。

| 源 | 本轮实测（含阳性标记） | 定案 |
|---|---|---|
| 浙江开放平台 | `POST /dopServer/dataCatalog/apiQueryPage`（body `{"pageNum":1,"pageSize":2}`，带 referer）→ 200 `{"success":true,"code":"2000","total":null,"result":{"records":[{"id":"FzK5…","sourceName":"浙江省公证员执业证版式文件","sourceCode":"S330000TAB0220…"}]}}` | **活跃待接**（真数据目录 API：免登录可编程，返回 sourceCode/数据元结构） |
| data.europa.eu SPARQL | `Accept: application/sparql-results+json` + 真查询 → 200 **SPARQL JSON**（`head`/`results`，bindings=2） | **活跃待接**（标准 SPARQL 端点，可 `dsModifyDate` 增量） |
| 四川统计局 | 首页 200 **不算**；顺首页链接找到 `/scstjj/c112116/sj.shtml` → 最新发布列表 → 月度页 `/scstjj/c112117/2026/9/16/073e…shtml`（131,580 B，**含 `<table>`，含「规模以上工业」**） | **活跃待接**（规整 HTML 表可 requests+parser 解析；须按首页链接发现，硬编码栏目路径会 404——本轮 `c105855/gzdt.shtml` 即 404） |
| NBS 流通领域（`dbcode=fsyd`） | `easyquery.htm?m=QueryData&dbcode=fsyd…` → **403** | **通道拦截**（与 `nbs-easyquery-blocked` 同源，维持 Wave 排除；换出口/集群指纹通道另议） |
| NBS 生产指数等其余入口 | 同域，同上 403 | 同上（并入同一条陷阱，不重复登记） |

**方法论收获**：四川统计局这条演示了「首页 → 栏目列表 → 月报表页」三级发现路径——
**首跳只是入口，证据必须在数据页**（含表、含指标名）。同时它反证了「硬编码栏目路径」
的坑：侦察簿记的 `c105855/gzdt.shtml` 已是 404，而首页现存的栏目是 `c112116/sj.shtml`。

---

# 欠账复测队列 · 第五批（凭据类 5 条，2026-11-10，64KB body + method/body 全传）

> 沿用第四批修好的两处 harness（body 窗口 64KB、method/body 一起传）。
> 本批重点：**凭据类不等于「探不到」**——3 条实测有明确体内答复，2 条被误以为要 key 其实不要。

| 源 | 本轮实测（阳性标记 / 体内答复） | 定案 |
|---|---|---|
| 中国货币网 LPR | `GET /ags/ms/cm-u-bk-currency/LprHis?lang=CN&startDate=…&endDate=…` → 200，`"rep_code":"200"` + `records[]` 含 `{"5Y":"3.50","1Y":"3.00","showDateCN":"2026-10-20"}` | **活跃待接（免 key）**——侦察簿记「LPR」但未验证；实测公开可读，无需鉴权 |
| 上清所月报 | `POST /shchapp/web/sdocClient/monthListPage`（body `{"pageNo":1,"pageSize":2}`，**只需 Referer**）→ 200 `{"flag":"0","data":[…]}`，标题含「表一 上海清算所固定收益产品业务总览」「表二 …发行量」 | **活跃待接（免 key）**——侦察簿记「需 JSESSIONID+Referer」，实测**只要 Referer**，JSESSIONID 非必需 |
| 高德开放平台 | `GET /v3/traffic/status/rectangle?rectangle=…` → **HTTP 200** 但体 `{"status":"0","info":"INVALID_USER_KEY","infocode":"10001"}` | **需免费 key**（200 是伪装，体内报错——第三例同型，见 F2） |
| KOSIS OpenAPI | `GET /openapi/Param/statisticsParameterData.do?apiKey=` → **HTTP 200** 但体 `{"err":"10","errMsg":"인증 KEY값이 누락되었습니다."}`（认证 KEY 缺失） | **需免费 key**（第四例同型） |
| NFRA 统计/处罚 | 侦察簿只记**路径片段**（`SelectByDocId?docId=` / `SelectDocByItemIdAndChild?itemId=`）；实测拼出的完整 URL 均 404；首页是 `meta refresh` 壳页（237 B），跳真首页后 59,813 B 内**无「行政处罚」字样**、无 `itemId` 线索 | **信息不足，需重侦察**：缺「完整端点 + itemId 取值」。不是不可得，是**我们没有可复现的请求** |

**方法论收获（第三条硬要求，收进陷阱清单）**：凭据类源分三种，不能一律按「要 key」归档——
① 真公开（LPR、上清所：免 key，且上清所连 JSESSIONID 都不需要）；
② 200 伪装（高德、KOSIS：200 + 体内 KEY 错误，必须阳性断言才判得出）；
③ 缺可复现请求（NFRA：只知道路径片段，拼不出端点 → 只能标「需重侦察」，
**不能标不可得**）。

---

# 欠账复测队列 · 第六批（5 条，2026-11-10，64KB + method/body）

| 源 | 本轮实测 | 定案 |
|---|---|---|
| PBoC 信贷收支表 | 栏目页 `diaochatongjisi/116219/116319/index.html` → 200，65,536 B；`<title>统计数据</title>`；页内 273 个 `<tr>` 全是**站点导航**（30 行有效文本为「信息公开/新闻发布/法律法规…」），**0 个条目链接** | **栏目页无静态数据**：真数据在 eportal/JS 通道（页面内嵌 `eportalCurrentPageId=116319`）。需侦察 eportal 接口，不能按静态 HTML 抓 |
| PBoC 贷款投向 | 同构（`goutongjiaoliu/113456/113469`）→ 200 | 同上，同一 eportal 机制 |
| PBoC 货政报告 | 同构（`zhengcehuobisi/125207/125227/125957`）→ 200 | 同上；**PDF 直链需从 eportal 列表取** |
| PBoC 区域金融 | 同构（年度合辑页 33 PDF）→ 200 | 同上 |
| 上清所 TRS 公告 | `POST /shchapp/web/disclosureForTrsServer/search`（body 试了 `ch/channelId/ch166/columnId=166` 四种键名）→ **HTTP 200** 但体 `{"success":false,"root":[],"totalProperty":"0","message":"请选择查询的栏目"}` | **200 伪装 + 参数未知**（第五例同型）：接口在，但栏目参数键名未探明。需从其前端 JS 取真实请求体，**不得猜参数** |

**方法论收获**：PBoC 四条的共性不是「不可得」，而是**「栏目页 200 + 有 table」也可能是空壳**
（表格装的是导航）。判据从「有 table」升级为「**有指向条目的链接（含日期段）**」——
本批 0 个条目链接，故判「无静态数据」。

---

# 决策记录：Eurostat 住宿价格指数**可得**（2026-11-10 定谳，推翻 golden 旧注记）

**旧记（`hotel-series-curation.md` 口径注记 3，2026-11-08）**：
> `prc_hicp_midx` 的 `coicop=CP11`（餐馆与住宿）与 `CP112`（住宿服务）实测均 **404
> `not available for dissemination`**；只有 `CP111`（餐饮服务）有 301 值（2000-12→2025-12）。
> 故**酒店线没有欧盟住宿价格指数**。

**本轮三参数实测（2026-11-10，fd-source-probe；每个 code 各跑一次，再按 unit 展开）**：

| coicop | 标签 | unit=I15 | unit=I05 | unit=RCH_A |
|---|---|---|---|---|
| CP11 | Restaurants and hotels | **200 / 313 期** 1999-12→2025-12 | 200 / 313 期 | 200 / **0 期** |
| CP111 | Catering services | **200 / 301 期** 2000-12→2025-12 | 200 / 301 期 | 200 / **0 期** |
| CP112 | Accommodation services | **200 / 301 期** 2000-12→2025-12 | 200 / 301 期 | 200 / **0 期** |

**定谳**：golden 那条「CP11/CP112 均 404」**不成立**——
- CP111 的「301 期 / 2000-12→2025-12」与 golden 记录**逐项吻合**，说明金记录与本轮测的是同一数据集、同一口径（`unit=I15`, `geo=EU27_2020`）；
- 在同一口径下 CP11 与 CP112 **均返回 200 且有值**；
- 唯一能让三者都显得"无值"的参数组合是 **`unit=RCH_A`**（年变化率未发布 → 三码皆 0 期）。golden 当时极可能用了它。

**落地状态（2026-11-10 主人确认后）**：
- ✅ 文档已更正：`fd-industry-data/docs/hotel-series-curation.md` 口径注记 3 / 注记 6 / 挂账 D5
  三处改为「可得」（commit `9ad2342`，已双推）
- ✅ `scripts/naming_gate_hotel.py` 的 `PAIRING` 常量加更正注释、**取值未动**
- ✅ **已落库（2026-11-10，含回滚点）**：概念 `hotel.eu.accommodation_price_index.monthly`
  + **301 期观测**（2000-12→2025-12，entity EU27_2020，source_used=eurostat-api，只增不改）；
  `provenance.pairing` 4 条 `missing → partial`（debt 收窄到 D1，新增 available_side.eu）。
  与 `hotel.eu.nights.monthly` 重叠 **180 个月**；幂等复跑 inserted=0。
  回滚点 `fd-industry-data/docs/rollback/hotel-pairing-before-2026-11-10.json`；
  决定记录 `openspec/changes/archive/2026-11-11-industry-source-solution-fleet/decisions/2026-11-10-hotel-accommodation-price-index.md`
- ✅ **golden 基线已同步（2026-11-10）**：`replay/golden-side.json` 的 N5 由
  「CP11/CP112 均 404」改为「**CP112 可得 301 期**」（`kind: probed_available`），
  原结论保留在 `superseded` 块里可追溯；陷阱 id 由 `…-absent` 改为 `…-available`
  （旧名会让人误读为"仍不存在"）。回归闸门复跑两次：**20 条全一致 / 漂移 0**
- ✅ **下游消费者核查（2026-11-10，全仓 grep）**：`replay/golden-side.json` **只有文档引用，
  **没有任何代码读取**（`golden-side`/`negative_conclusions`/`probed_404`/`hotel-replay-golden`
  四个关键词在 `*.py|*.sh|*.js|*.mjs|*.ts` 中命中数为 0）→ 不存在按 `probed_404` 穷举的分支，
  改 kind 无兼容性风险。但「无消费者 = 无校验」，故新增闸门
  `scripts/validate_golden.py`：schema 固定、**kind 闭集**（新增 kind 必须同时改校验器）、
  `superseded` 块四要素齐全（结论反转必须留痕）
- ⏳ **仍未做**：板面价量背离的渲染改造与规则调整（`pairing.state` 已改，消费方需验证）

**结论与影响**：
1. **住宿价格指数可得**，hotel 线可补价格面（`CP112` 301 期，可比 E2 夜数做价量背离）；
2. `hotel-series-curation.md` 的口径注记 3（「酒店线没有欧盟住宿价格指数」）与
   `provenance.pairing = {state: missing}` 的缺失侧标注**应作废并改为可得**；
3. 板面此前「价量背离」缺价格侧的处置需重做（属 hotel 线的后续单，不在本簿范围）。

**方法论教训**：`404 not available for dissemination` 不是"该指标不存在"，而是**该 code×unit 组合未发布**。
把一个 404 推广成"整条线没有价格指数"，是典型的「一个参数组合的结论被当成全集」。
本轮能翻案，靠的是**三 code × 三 unit 的矩阵**，而不是单点复测。

---

# 决策记录：上清所 TRS 公告**跑通**（2026-11-10，参数取自前端 JS，非猜测）

**旧状态**：侦察簿记「POST `/shchapp/web/disclosureForTrsServer/search`（ch166 流通要素/ch1…）」，
我此前试 `ch` / `channelId` / `ch166` / `columnId` 四种键名全部得
`{"success":false,"root":[],"message":"请选择查询的栏目"}` —— 那是**猜键名**的必然结果。

**反推过程（这才是正路）**：
1. 首页 411,246 B（需 2MB body 窗口才拿到 `<body>`，前 241KB 全在 `<head>`）
2. 导航 → `/xxpl/zxpz/`（专项品种，`pageTotal=3640`）
3. 该页加载 `../../images/cwbg.js`（61,663 B）——`grep disclosureForTrs` 命中
4. `cwbg.js` 的 `searchData()` 构造：
   ```js
   var params = {
     keyword: this.keyWord.trim().split(' '),   // 数组，且必须非空（前端拦「请输入关键字」）
     startDate: startTime, endDate: endTime,
     channelId: this.channelId,
     limit: this.pageSize, start: start
   };
   $.ajax({ url: shclearing.app_root + "disclosureForTrsServer/search",
            type: 'POST', dataType: "json", traditional: true, data: params, ... });
   ```
   → **form-urlencoded + traditional（数组按键重复）+ 不是 JSON**
5. `channelId` 由承载页内联脚本给出：`var channelId = "1205";`（`/xxpl/zxpz/`）

**实测结果**（`keyword=债券`）：

```
HTTP 200 · {"success":true, "totalProperty":1150, "root":[
  {"title":"关于调整印度尼西亚共和国2026年度第二期人民币债券(债券通)(品种三)簿记建档发行金额的说明",
   "url":"…/t20261110_1902568.html","publishDate":"2026-11-10","channelId":"1208"}, …]}
```

`keyword=评级` → 785 条；`keyword=2026` → 588 条。**通道可用，字段为 title/url/publishDate/channelId。**

**三个踩坑（写进陷阱清单）**：
1. body 必须是 `form-urlencoded`；用 JSON 会得「请选择查询的栏目」（服务端按表单参数绑定）
2. `keyword` 必须非空（前端有拦截），空串等于不查
3. **加 `accept: application/json, text/javascript, */*; q=0.01` 会返 HTML**；去掉即恢复 JSON —— header 形状敏感，照抄前端时不要自创

**方法论**：这一条此前被我判成「200 伪装 + 参数未探明」。真相是**参数可从公开前端 JS 完整反推**——
先找承载页 → 找它加载的业务 JS → 读 `searchData()` 的 params 构造 → 找页面内联变量。
「参数未知」的正确处置是**读前端**，不是穷举键名。

---

# 第六批补充定案：PBoC 四条**确认为 eportal 空壳**（2026-11-10，按同一手法验到底）

用反推 TRS 的同一手法（读页面 JS / 找 portlet 端点）把 PBoC 四条验到底：

| 检查 | 结果 |
|---|---|
| `/diaochatongjisi/116219/116319/index.html`（信贷收支） | 200，`<title>统计数据</title>`，273 个 `<tr>` 全是站点导航 |
| 页面内条目链接（`/t20YYYYMM_xxxx.html`） | **0 个** |
| 服务端渲染的条目标题锚文本（含"收支表/统计表/报告/数据"） | **0 个** |
| 页面内 `eportal` portlet 地址 | 仅 `/eportal/ui?pageId=…`（UI 壳，实测 **404**） |
| 页面内唯一接口 | `https://wzdig.pbc.gov.cn/search/pcRender`（站内**搜索**表单，非数据目录） |

**定案：PBoC 信贷收支表 / 贷款投向 / 货政报告 / 区域金融 四条均无法静态取数。**
数据由 eportal portlet 在浏览器端异步装配，静态 HTML 里只有导航。
要接须先打通 eportal 的 portlet 数据接口（页面未暴露明文端点）→ **需重侦察，非"不可得"**。

**与 TRS 的对照（同一天、同一手法、不同结果）**：
- TRS 能反推成功，是因为业务 JS `cwbg.js` 里**明文写着** `$.ajax({url: app_root+"disclosureForTrsServer/search", data: params})`；
- PBoC 反推不出来，是因为它的数据流走 portlet 容器运行时装配，页面里**没有任何明文端点**。
> 判据：**"能否从公开前端 JS 读到明文请求构造"决定了这条路走不走得通**。
> 读得到 → 可反推（TRS）；读不到 → 只能重侦察，不得穷举参数（PBoC）。

---

# 欠账复测队列 · 第七批（4 条，2026-11-11，免 key JSON 面；含 1 条结论反转）

> 取「accepted + 无证据 + 未落地」的 29 条空白里最省事的一组：全部免 key、GET、JSON 体、
> 有可机器判定的阳性标记。探针版本与第六批同（64KB body）。

| 源 | 本轮实测 | 定案 |
|---|---|---|
| Treasury FiscalData | `GET /services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash?page[size]=1` → **200**，体 `{"data":[{"record_date":"2005-10-03","account_type":"Federal Reserve Account",…`（2,540 B）；另测 `v1/accounting/od/rates_of_exchange` → 200、`v2/accounting/od/avg_interest_rates` → 200，三条均 ok | **活跃待接（推翻第一批判定）** —— 详见下方反转记录 |
| data.gov.uk | `GET /api/3/action/package_search?rows=1` → **200**，体 `{"help": …, "success": true, "result": {…`（25,289 B） | **活跃待接**（CKAN 标准动作，可直接编程取元数据与资源分布） |
| OpenDataSoft | `GET /api/explore/v2.1/catalog/datasets?limit=1` → **200**，体 `{"total_count": 102983, "results": [{"visibility": "domain", …` | **活跃待接**（10.3 万数据集聚合目录，免 key；做发现层，与 data.gov 目录同类） |
| GDACS | `GET /gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ&fromDate=2026-10-01&toDate=2026-10-31` → **200**，体 `{"type":"FeatureCollection","features":[{"type":"Feature","bbox":[…` | **活跃待接**（免 key GeoJSON，含坐标与 alertlevel；灾害事件面，fromDate/toDate 可回溯） |

## 反转记录：Treasury FiscalData「端点漂移、不可出单」（第一批判定）作废

**原结论（第一批判定，2026-11-10）**：
> 侦察簿所记 v1 路径与 v2 全 404（HTML 404 页）；`transparency.treasury.gov` 302
> → **端点路径漂移，需重侦察**；当前不可出单

**推翻日**：2026-11-11

**证据（本轮实测，三条独立端点，全部 200 且体首为 `{"data":[`）**：

| 端点 | 状态 | 体首 |
|---|---|---|
| `v1/accounting/dts/deposits_withdrawals_operating_cash` | 200 | `{"data":[{"record_date":"2005-10-03","account_type":"Federal Reserve Account",…` |
| `v1/accounting/od/rates_of_exchange` | 200 | `{"data":[{"record_date":"2001-03-31","country":"Afghanistan","currency":"Afghani",…` |
| `v2/accounting/od/avg_interest_rates` | 200 | `{"data":[{"record_date":"2001-01-31","security_type_desc":"Marketable",…` |

**最可能的成因（不为结论服务，只作解释，未证实）**：第一批当时的 404 是 HTML 页，
与现在的 JSON 面不同 —— 更像是当时打到了**错误的服务名**（`fiscal_service` 之后那一段是
数据集路径，拼错就落 404 HTML），而不是 API 整体下线。按约束③「选可验证更严的一侧」：
现在有三条可逐字段复核的 200，采信正向观测；旧判定的"不可出单"作废。

**决定记录**：本条无需单独立 change 级决定记录——它不涉及跨消费者共享口径列，也不改变
「接不接」的业务判断（原本就是 accepted）；只更正事实层结论，故就地留痕（本节）。

**仍须注意**：`transparency.treasury.gov` 的 302 与本 API 是**两个面**，不要因为 API 活了
就认为那个门户也活了；两者判据各自独立。

## 本批口径

- 四条均**未改** candidates 的 accepted 状态（复测不改「接不接」，只把"有没有证据"从空补成有）
- 阳性标记均取**体内结构**（`"data":[` / `"success": true` / `"total_count"` / `FeatureCollection`），
  不取状态码单独作证——200 伪装在这个仓已有六例（TRS/PBoC/amap/KOSIS 等）

## 本批的口径纠偏：99 条「无证据」里只有 7 条是真空白

做第七批时先入为主地把「accepted + 无证据」当成待办队列，得到 99 条。实际统计后发现这是个**口径错误**：

| 口径 | 数 | 说明 |
|---|---|---|
| mention（每张表一行） | 199 | 同一个源会在「★接 候选总表」和「欠账复测队列」各出现一次 |
| **唯一源**（按名归一） | **168** | 业务上真正要数的是这个 |
| accepted mention | 144 | |
| accepted 唯一源 | 128 | |
| 无证据且未落地 mention | 29 | 看似待办 |
| 其中同族已有证据（重复 mention） | 22 | **不是待办**，兄弟行早就测过 |
| **真空白（同族无任何证据）** | **7** | 只有这 7 条需要探测 |

真空白 7 条（截至 2026-11-11）：`nbs-流通领域生产资料价格`、`kosis-零售-线上购物表`、
`world-bank-data360-mcp`、`nfra-统计-excel-附件`、`nfra-处罚公开`、`lpr`、`理财产品查询`。
特征也清楚：**5 条需要凭据或特殊通道**（KOSIS 免费 key、data360-mcp 是 pip 包、
两条 NFRA 走 docId 参数链、LPR 与理财走 chinamoney/lcw 的 JS 加密通道），
不是"抓一下就有"的类型。

**已落进代码，不靠记性**：`extract_candidates.py` 的 `summarize()` 现在同时报
mention / 唯一源 / 真空白，self-test 钉住 `_name_key` 的全半角括号与大小写归一。
判据纪律：**先按名归一再决定要不要跑探测**——否则会把重复 mention 当欠账，白跑一轮
还会往漏斗里塞重复行（本轮就塞了 4 条，接受这个代价是因为复测批次的既有惯例是
"一批一组新行"，且新口径已能让读数不再失真）。

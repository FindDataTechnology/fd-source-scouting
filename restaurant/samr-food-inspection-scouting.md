# samr-food-inspection 侦察记录（国家市场监督管理总局食品安全监督抽检公告）

- 侦察日期：2026-11-07
- 侦察人：samr-food-inspection 建单 agent
- 结论：**可接，已生成单静默合入，待人工点亮**（spiders/samr-food-inspection/）

## 端点

| 端点 | 状态 | 说明 |
|---|---|---|
| `https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/spcjs/`（食品抽检司栏目） | 200 | **列表入口（壳页）**。博达 jPaas CMS：列表由前端 `AuthorizedRead/unitbuild.js` 渲染，壳页静态 HTML 内嵌完整调用参数（webId/pageId/tplSetId/tagId/url） |
| `https://www.samr.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=…&tplSetId=…&pageType=column&tagId=内容区域&editType=null&pageId=…&paramJson={"pageNo":N,"pageSize":20}` | 200 | **列表数据 API**（JSON `data.html` 片段）。分页参数**必须放 `paramJson`**——把 `pageNo=2` 直接放 URL 参数实测仍返回第 1 页 |
| `https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/spcjs/art/<年>/art_<hash>.html` | 200 | **正文页**（服务端整页渲染）：正文块 `div.Three_xilan_07`、附件 `ul.contentLeft0102box`、meta ArticleTitle/PubDate/Description |
| `https://www.samr.gov.cn/hd/zjdc/`（工单 lead：征集调查） | 200 | 200 但**内容不符**——是「征集调查」栏目，非抽检公告；其「食品安全」子块也是 JS 壳，无抽检列表 |
| `https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/tssps/`（特殊食品司） | 200 | 200 但是同款 JS 壳（AuthorizedRead），特殊食品类抽检在此栏目，本单元未接 |
| 候选主机 `samsu/cjpv/spcjs/so.samr.gov.cn` | DNS 解析超时 | 专网/内网或已下线，公网不可达；**「抽检公布查询页」不可作为公网采集面**。正文里的查询入口 `https://spcjsac.gsxt.gov.cn/` 属 gsxt 域（另行评估，本单元未依赖） |

## 直连/代理裁决

**仅直连**（国内政府站点，scouting book 代理规则不适用）。全程未用代理，无频控观测。
TLS 为 CFCA EV（issuer CN=CFCA EV OCA，notAfter=2027-01-09），按仓内惯例 verify=False。

## 鉴权

无。无 token/cookie/验证码/UA 门槛；retries=1 单次尝试、timeout=30s、
请求间 0.5–0.9s 抖动，未触发任何拦截。

## 周期

不规则（`data_period: irregular`）。实测 2026-01~10 共 16 条，月均 1–3 条、突发成批
（2026-06 月内 4 条）；栏目里另有季度/年度综合统计通告（2022-2024 每季/每年 1 条）。
轮询频率取 weekly（保证周内捕获，成本极低）。

## 历史深度

- 列表 API `count=228`（rows=20 → 12 页）；**末页（pageNo=12）最早条目 2019-02-22**
  （「关于12批次食品不合格情况的通告」）。列表对 2019 年以来全量公告完整留存。
- pageSize 探到 ~100 封顶（pageSize=250 实回 99 条，2022-01-14 → 2026-10-12）。
- 单元默认 `max_pages=2`（≈40 条候选）；需深历史调大即可，采集逻辑无需改动。

## 栏目构成（99 条实测清点）

不合格批次通报/通告 64（**总局只公开发布不合格结果**）+ 快检/补充检验方法公告 14 +
其他 21（名录/废止/召回/对人大代表建议的答复/季度年度综合统计）。
→ `result_category` 口径里 `qualified` 是防御性档（栏目内无实例）。

## 字段级口径定义（任务 2.4，与 spider.py TITLE_RULES/BODY_RULES 及 README 规则表逐字一致）

- `result_category`（标题规则优先，首条命中即返回；标题判不出才用正文兜底；正文 = 正文块 + 附件名）：
  - `unqualified`：标题命中 `不合格`（兜底正文 `检出[^。]{0,14}批次[^。]{0,8}不合格|不合格食品|不合格产品信息`）——具体批次抽检不合格通报/通告；
  - `qualified`：标题 `抽检[^。]{0,20}合格`（兜底正文 `全部合格|均未检出`）——全部合格类，防御性；
  - `other`：标题命中 `快速检测|补充检验方法` → 检验方法类；`非食用物质名录|废止|工作规范|管理规定|建议的答复|核查处置|召回` → 制度/处置/答复类；`抽检情况` → 季度/年度综合统计（兜底正文 `(季度|年度|半年|上半年)[^。]{0,12}抽检|抽检情况`）；
  - 判不出 → `None`（不猜）。
- **矛盾处理**：标题与正文同时给出抽检结果类结论（都在 {unqualified, qualified}）且相左
  → **跳过该行 + warning 留痕**，不猜一个。`title=other` 是体裁结论，与正文引用
  「不合格」字样**不构成矛盾**（如建议答复复述抽检工作），照常按 other 出行。
- `restaurant_related`：标题+正文+附件名命中 `餐饮|食堂|餐馆`（**附件名是批次通报分类
  覆盖面唯一载体**——正文块常不含「餐饮」，而「附件9 餐饮食品监督抽检不合格产品信息.xlsx」
  只在附件区）。纯标注，不过滤。
- `notice_date`：列表页 contenttime `YYYY-MM-DD` 锚定；缺失回退正文 meta PubDate 日期部分；
  两者不一致保留列表页日期 + warning 留痕。
- `body_digest`：正文块去空白前 200 字符；缺失回退 meta Description；再缺 None。
  下游「抽检不合格过滤」凭 result_category + body_digest 即可字段级过滤，无需全文重爬。

**人工判定 vs 解析器：6/6 一致**（52 批次通报→unqualified、13 项快检方法公告→other、
跨境电商召回公告→other、35 批次通告→unqualified、2024Q3 季度通告→other、
7864 号建议答复→other；逐条对照见 spiders/samr-food-inspection/README.md）。

## 接入成本

低。壳页 → 列表 API（JSON 包 HTML 片段）→ 正文页三跳，免鉴权、服务端渲染，
scrapling+lxml 标准解析；无 PDF/表格解析。单次 limit=20 全程 ~22 请求、约 20s（含限速）。

## 关键坑

1. **工单 lead 落空 + 专网查询页不可达**：`/hd/zjdc/` 是「征集调查」不是抽检公告；
   「食品安全抽检公布」的专用查询系统（samsu/cjpv 子域、spcjsac.gsxt.gov.cn）公网
   DNS 不可达或属 gsxt 域。**可采集面 = 政务公开「食品抽检司」栏目**（spcjs），
   靠站内导航 + 搜索 API 关键词命中文稿 URL 后回溯到栏目定位。
2. **jPaas 双层壳**：列表在 `data.html` JSON 里、分页必须走 `paramJson`
   （pageNo 放 URL 参数无效）；壳页解析失败按硬失败抛 RuntimeError（fail loudly）。
   webId/pageId 每次运行从壳页实时解析，不硬编码，站点换 pageId 不受影响。
3. **分类覆盖面只在附件名**：批次通报正文块常不含「餐饮」字样，「餐饮食品」等品类
   只出现在附件 xlsx 文件名里——restaurant_related 必须把附件名纳入检索面；
   若站点未来不发附件，该列会系统性失真（README 遗留风险 4）。

## 首爬

2026-11-07 真实运行 `run_samr_food_inspection(limit=20)`：**20 行 / 20 篇公告**
（unqualified 17 / qualified 0 / other 3；restaurant_related True 17；无 None 字段；
golden 重放 ok=True, rows=20, diffs=[]）。样例行见 spiders/samr-food-inspection/README.md。

## 状态

**已接入 · 已点亮（2026-11-07 波1 收口）**

- 试跑：`run samr-food-inspection` success **100 行**（通告，2022-01-07 → 2026-10-12；
  `max_pages=6` 深抓；列表日期锚定，正文 meta 日期漂移留痕但不改锚）
- 点亮：`schedule: "27 6 * * 3"`（每周三 06:27）
- 观测：**不写数值序列**（事件面）——`scripts/restaurant_extractors/samr_food_inspection.py`
  每次运行输出分类分布与消费方说明；数值化（如「每月通告数」）属聚合造假，违反
  observation 契约「每个写入值必须是真实 payload 值」
- 字段级口径实证（任务 2.4）：100 条实测 `unqualified=65 / qualified=0 / other=35`，
  `restaurant_related=true` 45 条；人工抽样 6 条判定一致（见上文规则表）
- 口径守卫：golden 001 replay ok=True（rows=20）
- lints：validate_manifests 0 violations；conformance_gate PASS 124 units 0 violations

# customs-agri 侦察报告

- 对象：海关总署（GACC）农产品进出口月度统计，HS 01-24 章
- 探测时间：2026-11-07 16:18-16:20 UTC（北京时间 2026-11-08 00:18-00:20）
- 方式：`curl --noproxy '*'`，已 unset 全部 proxy 变量；未登录、未提交表单、未绕防护
- 探测点：8 个（7 个 curl + 1 次搜索引擎站点检索）

## 结论

**不可得（直连）。** 海关总署三个相关主机全部前置加速乐（JSL / X-Via-JSL）防护层，任何无 JS 执行的 HTTP 请求都拿不到业务内容：

- `www.customs.gov.cn` → HTTP 412（http）/ 504（https），响应头 `X-Via-JSL`
- `stats.customs.gov.cn` → HTTP 412，响应头 `X-Via-JSL`，下发 `__jsluid_h`
- `query.customs.gov.cn` → HTTP 503，响应头 `X-Via-JSL`，下发 `__jsluid_h`
- 旧统计平台 IP `43.248.49.97` → TCP 连接超时

因此**未能取得任何页面正文、附件 URL 或一条真实数据样例**。本报告中标「未验证」的字段均无实测支撑，不可当作事实使用。

归类：**需查询平台鉴权 + 防护层 → 实为「不可得」**。不是数据不公开（海关统计月报本身是公开发布物），而是发布面被 WAF 挡在 JS 挑战之后，按分诊纪律不得逆向。

## 既有单元经验

`fd-industry-data/spiders/customs-xborder-retail/`（跨境电商零售 9610/1210）先于本次侦察落地，结论一致：

- 文件头注释已记录（2026-11-03 实测）：`stats.customs.gov.cn` 全站 JSL，curl 直连返回 504 / 412；`www.customs.gov.cn` 同 JSL，统计分析栏目同样 504/412；两站无公开无鉴权 API。
- `spider.py` 实现了 `_has_jsl_protection()`（查 `X-Via-Jsl` 头、`__jsluid_s/h`、`__jsl_clearance_s` cookie、正文关键词）与 `_classify_error()`，命中即归因 `upstream-protection`，返回单条结构化错误行而非空列表。
- 已有测试 `fd-industry-data/tests/test_xb_spider_attribution.py` 固化该归因（412 → upstream-protection）。
- `manifest.yaml` 为 `scanner_mode: upstream-curated`，状态实质是「契约层待人工」。
- 另有旁证：`fd-cn-report/ministry_stats_client.py:57` 的 `gacc` 条目 `stat_path = "/customs/302249/zfxxgjbgjk/"`，源码注释自标 `# undocumented - verify live`，同样是**未验证的猜测路径**，点亮会撞同一面墙。
- 侦察簿 `data-source-scouting/INDUSTRY-DATA-SOURCES.md:105` 已把 `stats.customs.gov.cn` 列入「放弃」清单（记作 412 墙）。
- `fd-industry-data/scripts/preclassify_stock.py:155` 把该单元标为 `s=park`（保留代码等出口）。

本次实测**复现并确认**了上述全部结论，无新增可用通道。

## 探测记录

| # | URL | 方法 | 状态码 | 大小 | content-type | 判定 |
|---|---|---|---|---|---|---|
| P1 | `https://www.customs.gov.cn/` | GET | 无（curl 60） | 0 | — | TLS 证书链含自签证书，校验失败；疑似链路中间设备 |
| P2 | `http://stats.customs.gov.cn/` | GET | **412** | 未下载（chunked） | `text/html; charset=utf-8` | JSL 挑战页；`X-Via-JSL: b66aa29,-`，下发 `__jsluid_h` |
| P3 | `http://query.customs.gov.cn/` | GET | **503** | 326 B | `text/html; charset=us-ascii` | JSL 拦截；`X-Via-JSL: b126a64,-` |
| P4 | `http://www.customs.gov.cn/` | GET | **412** | 未下载（chunked） | `text/html; charset=utf-8` | JSL 挑战页；`X-Via-JSL: b0c367f,-` |
| P5 | `https://www.customs.gov.cn/`（`-k` 跳证书） | GET | **504** | 5641 B | `text/html` | JSL 网关超时页；`X-Via-JSL: b126a64,-`，下发 `__jsluid_s` |
| P6 | `http://www.customs.gov.cn/customs/302249/302266/302267/index.html` | GET | **412** | 未下载（chunked） | `text/html; charset=utf-8` | 栏目级路径与首页同墙；`X-Via-JSL: 074bd60,-` |
| P7 | `http://43.248.49.97/`（旧统计查询平台 IP） | GET | 无（curl 28） | 0 | — | TCP 连接 20s 超时 |
| P8 | `cn.bing.com` 站内检索 `统计月报 site:customs.gov.cn` | GET | 302→200 | — | — | 仅返回 `http://stats.customs.gov.cn/`，无其他栏目/附件直链 |

说明：P1 的证书异常与 P5 的 `-k` 是同一主机同一次可达性判定，P5 才是有效状态码。P8 为搜索引擎侧发现，非海关站点探测。412/503/504 三类响应体均未逐字核验（探测纪律限制），但 `X-Via-JSL` 响应头已足以判定防护层。

## 数据通道

| 项 | 实测结果 |
|---|---|
| 列表 URL | **未验证**。候选 `/customs/302249/302266/302267/index.html`（P6）被 412 拦截，未取得任何列表 HTML |
| 附件形态 | **未验证**。未能抵达任何附件；无法确认是 xls / xlsx / pdf / 内嵌 HTML 表 |
| 字段 | **未验证**。本报告不提供字段表，以免编造 |
| 真实样例 | **无**。未取得任何月份、任何章别的金额数值 |
| HS 章级可取性 | **未验证**。无法判断上游是给到 HS 章（01-24）还是仅总值 |
| 更新周期 | **未验证**。无发布页可比对 |
| 可回溯深度 | **未验证**。 |

## 坑位

1. **防护在主机层，不在路径层**：换任何 `customs.gov.cn` 子路径都是同一张 412，绕路径无意义（P4/P6 同码）。
2. **http 与 https 错误码不同**：同一主机 http 给 412 挑战页，https 给 504 网关超时。只看一种协议会误判为「站挂了」。
3. **TLS 证书链异常**：`www.customs.gov.cn` 在本次链路下报「self signed certificate in certificate chain」。这是**链路中间设备**特征，不是站点证书问题；用 `-k` 后得到 504，说明不是证书挡路，而是 JSL。生产代码若开 `verify=True`，会在这里先失败一次，错误分类会被误判成 network 而非 protection。
4. **旧 IP 已成死路**：`43.248.49.97` 是 2018 前后统计查询平台地址，现已超时，不要再当备选。
5. **搜索引擎只索引到查询平台**：说明统计月报的栏目页/附件页基本不进公开索引，靠检索找直链这条路走不通。
6. **`fd-cn-report` 的 gacc 路径是猜的**：`/customs/302249/zfxxgjbgjk/` 无实测支撑，若被点亮会以 network/upstream 错误告警，而不是 protection，容易误导排障。
7. **静态附件未必免墙**：同主机静态资源通常一并走 WAF（未单独验证，按同类政府站经验，标为待验证）。

## 建议

1. **不新增海关农产品 spider**。既有 `customs-xborder-retail` 的 `upstream-protection` 归因已正确，继续 park，不做无意义重试。
2. **不要尝试过 JSL**：需要执行 JS 拿 `__jsl_clearance_s`，属于绕防护，超出分诊纪律；也不要用 Browser Use 去取 cookie 再回灌。
3. **农产品 HS 01-24 月度改走替代源**：
   - UN Comtrade / BACI（HS 双边贸易，已在侦察簿 C 类；可按 reporter=China、HS 01-24 聚合）；
   - 农业农村部、商务部转载的海关口径月度进出口数据（需另立探测，本次未测）；
   - FAO / USDA FAS（口径不同，作交叉校验）。
4. **若必须用海关原始口径**：只能走「契约层人工」——人工在浏览器完成 JSL 挑战后，人工下载统计月报附件，落成 golden 样本，再评估是否值得做半自动通道。届时需重新探测附件形态与章级粒度。
5. **顺手修一处误导**：`fd-cn-report/ministry_stats_client.py` 的 `gacc.stat_path` 建议标注 `# blocked by JSL (412/504), verified 2026-11`，避免后续有人按该路径排障。

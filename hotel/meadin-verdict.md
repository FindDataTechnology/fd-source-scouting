# 迈点（meadin.com）MBI 去留裁决（实测 2026-11-08，任务 2.2）

## 裁决：**放弃 · 显式不可得**

## 为什么不是「502 超时」

上一轮记的是「代理与直连各测一轮，502 / 12s 超时」。本轮复测发现**那个结论是错的**——
502 不是站点不可用，是 WAF 对**裸 `curl` UA**（无 `Accept` / `Accept-Language` / `Accept-Encoding`）的拒绝。
补全浏览器头后站点**立刻 200，0.25 秒返回**。所以必须把裁决理由改写成真实障碍。

## 实测矩阵（2026-11-08，本机直连，系统代理已关闭 `HTTPEnable: 0`）

| 传输 | 请求 | 结果 |
|---|---|---|
| 裸 curl | `GET https://www.meadin.com/` | **502** / 227 B / 12.56 s（Tengine 网关错误页） |
| 裸 curl | `GET https://www.meadin.com/report/` | 502 / 227 B / 12.57 s |
| 裸 curl | `GET https://meadin.com/`（无 www） | **000** / 4.45 s（连接失败） |
| 裸 curl | `GET https://m.meadin.com/` | 502 / 12.62 s |
| 裸 curl | `GET https://203.107.63.30/` + `Host: www.meadin.com` | 502 / 12.64 s |
| 代理 127.0.0.1:7892 | 任意 | **000 / 0.0002 s** —— 代理端口未监听（`scutil --proxy`：`HTTPEnable 0`），本轮**无法测代理** |
| 完整浏览器头 + HTTP/2 | `GET https://www.meadin.com/` | **200 / 8,235 B / 0.28 s** ✅ |
| 完整浏览器头 | `GET https://www.meadin.com/report/` | 200 / **8,235 B**（同一挑战页） |
| 完整浏览器头 | `GET https://www.meadin.com/sitemap.xml` | 200 / **8,235 B**（同一挑战页） |
| 完整浏览器头 | `GET https://www.meadin.com/robots.txt` | 200 / **8,235 B**（同一挑战页） |

## 真实障碍：JS Cookie 挑战（不是鉴权、不是付费墙、不是超时）

200 返回的 8,235 字节**不是内容**，是反爬挑战页：

```html
<html>
<body onload="check()">
	<input type="hidden" name="parm_0" value=-2144972356 id="parm_0">
	<input type="hidden" name="parm_1" value=2009091025  id="parm_1">
	<script type="text/javascript">
    function Z(){var U=['setDate','CPBoA','EuWuh',...
```

特征：`body onload="check()"` + 两个隐藏 `parm_*` + 混淆 JS 数组 + `document.cookie` 拼装
（`';path=/'`、`';expires='`、`toGMTString`）—— 典型**瑞数 / 加速乐式动态 Cookie 挑战**。

**判定依据（关键）**：`robots.txt` 与 `sitemap.xml` 这类静态文件也返回**同一个 8,235 字节挑战页**，
说明 WAF 在**站点入口拦截全部请求**，不是「某个页面要登录」。因此：

- 没有可以绕过的「公开静态路径」；
- 没有可用的 RSS / JSON API 面（未发挑战前的请求全部 502，发了就全被挑战）；
- 唯一通路是**执行 JS 解出 cookie**，即需要无头浏览器 / 挑战求解器。

## 为什么不做

1. **红线邻近**：JS 挑战求解属于「绕反爬」，不是「接公开数据」。本仓爬虫单元一律只做
   公开、可直连、无鉴权的面。
2. **平台定位不符**：迈点 MBI 是**商业指数产品**，指数本身就带付费属性；即使解了挑战，
   拿到的也只是营销页上的排名摘要，不是可校验的数据面。
3. **有等价替代**：品牌榜/集团榜可由**中国饭店协会年度报告**（`group2026.pdf`，文本层完整、
   TOP50 整表可抽，见 `ctha-report-scouting.md`）覆盖，且协会口径**可引用、可审计**。
   迈点 MBI 的独有价值（月度品牌指数）**不足以**支撑引入 JS 挑战依赖。

## 解锁条件（两段式留痕）

**若将来要接，前置条件必须同时满足：**

1. 迈点开放**公开 API 或 RSS**（或出官方数据授权），使请求无需执行 JS 即可获得内容；或
2. 用户明确授权使用无头浏览器通道（`browser-use` 插件），并由**主代理**而非子代理执行
   （子代理禁用 Browser Use 是本仓纪律），且明确接受「绕挑战」的合规风险。

在此之前，板面与工具面呈现为 `unavailable / anti-bot-js-challenge`，**不放 0、不拿协会数替代**。

## 对现有资产的连带修正

- 侦察簿原「迈点 502 / 12s 超时」一句，应改为「WAF 对裸 UA 返 502；补全头后为 JS 挑战」。
- 本条不改任何 `spiders/` 产物——迈点从未建单。

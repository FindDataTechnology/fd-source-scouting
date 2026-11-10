# sugar-cotton 侦察报告

站点：中国糖业协会 `www.chinasugar.org.cn`（211.149.156.139）、中国棉花信息网/棉花协会 `www.chinacotton.org`（59.110.18.27）
侦察时间：2026-11-08 ｜ 全程**直连、未走代理**（7890/7892 实测不可用，未重试）｜ 只做 HTTP 探测，未绕反爬
探测点：8 个（糖 4 / 棉 4），单点 ≤3 次尝试

## 结论（两行）

**棉：可接入**——HTTPS 443 端口直接拒绝，但 **HTTP 明文 80 完全正常**（200，IIS 7.5，48KB 首页，栏目与月度报告齐全），立即可用，只需允许明文。
**糖：不可达（非网络不可达，是站点自身 vhost 未就绪）**——TCP 443 可连、TLS 握手能走完，但证书是**别的域名**（CN=5-8lab.com）；HTTP 层拿到 nginx **403**。非 DNS、非墙、非代理问题。

## 糖业协会探测

| # | URL | 阶段 | 错误信息 / 状态码 | 判定 |
|---|-----|------|-------------------|------|
| 1 | `https://www.chinasugar.org.cn/` | TLS 握手完成 → 证书校验 | exit 60 `SSL: no alternative certificate subject name matches target host name` | **证书不匹配** |
| 2 | `http://www.chinasugar.org.cn/` | HTTP | **403 Forbidden**，`Server: nginx`，79ms | 端口通，应用层拒绝 |
| 3 | `https://chinasugar.org.cn/`（无 www） | TLS 证书校验 | exit 60，同上证书错误（170ms） | 与 #1 同因，无 www 也同证 |
| 4 | `curl -v https://www.chinasugar.org.cn/` | 全链路 | 见下关键行 | 定位在**证书/vhost**，非网络 |

关键 `-v` 行：

```
* Connected to www.chinasugar.org.cn (211.149.156.139) port 443
* TLSv1.2 (IN), TLS handshake, Certificate (11):
* SSL connection using TLSv1.2 / ECDHE-RSA-CHACHA20-POLY1305
*  subject: CN=5-8lab.com
*  expire date: Jan 10 09:37:54 2027 GMT
*  issuer: C=US; O=Let's Encrypt; CN=YR2
*  subjectAltName does not match host name www.chinasugar.org.cn
curl: (60) SSL: no alternative certificate subject name matches target host name
```

补充（第 4 点的延伸验证）：加 `-k` 跳过证书后握手走通、`ALPN` 接受 `http/1.1`，但服务端仍回
`HTTP/1.1 403 Forbidden / Server: nginx`。即**跳证书也拿不到内容** ⇒ 该 IP 上的 nginx 未为本 Host 配置站点。

## 棉花探测

| # | URL | 阶段 | 错误信息 / 状态码 | 判定 |
|---|-----|------|-------------------|------|
| 1 | `https://www.chinacotton.org/` | TCP（443） | exit 7 `Connection refused`，53ms | **443 端口未监听（RST）** |
| 2 | `http://www.chinacotton.org/` | HTTP | **200 OK**，`Microsoft-IIS/7.5`，`X-AspNet-Version: 4.0.30319`，48,582B，333ms | **正常可用** |
| 3 | `https://chinacotton.org/`（无 www） | TCP（443） | exit 7 `Connection refused`，117ms | 同 #1，无 www 也拒 |
| 4 | `curl -v https://www.chinacotton.org/` | 全链路 | 见下关键行 | 定位在 **TCP RST**，未进 TLS |

关键 `-v` 行：

```
*   Trying 59.110.18.27:443...
* connect to 59.110.18.27 port 443 from 192.168.1.4 port 63646 failed: Connection refused
* Failed to connect to www.chinacotton.org port 443 after 53 ms: Couldn't connect to server
curl: (7) Failed to connect to www.chinacotton.org port 443 after 53 ms
```

### 数据栏目（HTTP 80 实测，首页 200）

站点标题 `棉花产业经济`，国家现代棉花产业技术体系产业经济研究室主办（地址：北京西城砖塔胡同 56 号，京ICP备10049099号-6）。

| 栏目 | 列表 URL（实测存在） | 形态 / 周期 |
|------|----------------------|-------------|
| 棉花市场监测报告 | `http://www.chinacotton.org/articleList.aspx?sort=2` | 双月（1-2月、3-4月…7-8月）HTML |
| 中国棉花供需平衡表 | `http://www.chinacotton.org/articleList.aspx?sort=6` | 月度，止于 2023-09 |
| 国际市场价格与贸易分析 | `http://www.chinacotton.org/articleList.aspx?sort=1` | 月度 |
| 全国棉花生产监测报告 | `http://www.chinacotton.org/articleList.aspx?sort=5` | 月度 |
| 产业经济研究（论文/分析） | `http://www.chinacotton.org/articleList.aspx?sort=4` | 不定期 |
| 会议/调研动态 | `http://www.chinacotton.org/articleList.aspx?sort=3` | 不定期 |

详情页规则：`/articlePage.aspx?articleID=<id>`（`target=_blank`，HTML）。

**一条真实样例**（首页 200 实测抓到）：
`http://www.chinacotton.org/articlePage.aspx?articleID=409` → 《2025年7-8月棉花市场监测报告》

同页可见真实条目：`2025年5-6月棉花市场监测报告`、`2025年1-2月棉花市场监测报告`、`2023年9月中国棉花供需平衡表`、`2025年8月全国棉花生产监测报告`、`2025年8月棉花国际市场价格与贸易分析`。
（详情页正文形态/是否含附件：**未验证**——受 8 探测点上限约束，未再抓 articlePage。）

## 归因

- **糖业协会：TLS 证书不匹配 + vhost 未配置（应用层 403）**
  - DNS 正常（A → 211.149.156.139），TCP 443 **可连**，TLS 握手**完整走完**（TLSv1.2 / ECDHE-RSA-CHACHA20-POLY1305）。
  - 失败点单纯是 **证书校验**：服务端出示 `CN=5-8lab.com`（Let's Encrypt YR2，有效期至 2027-01-10），SAN 不含 `chinasugar.org.cn`。这是**同 IP 多站点共享、该域名 vhost 未绑定证书**的典型现象——211.149.156.139 这台机上实际部署的是 `5-8lab.com`。
  - HTTP 层同样 403（nginx），说明请求落到了默认/其他 vhost 后被拒。**不是 GFW，不是 DNS 污染，不是代理问题，也不是 TLS 协议版本过低**（TLS1.2 正常协商）。
  - 未验证项：403 是否随 UA/Referer 变化——依「不绕过反爬」纪律**未做 UA 伪装测试**。
- **棉花：TCP 443 端口未监听（fast RST）**
  - DNS 正常，TCP 层 53ms 内 `Connection refused`（主动 RST，非超时）→ 443 压根没服务在听，未进入 TLS 阶段。
  - 该站仅部署 HTTP/80（`Microsoft-IIS/7.5` + ASP.NET 4.0.30319），**从未启用 HTTPS**。

## 障碍与解锁条件

**糖业协会**
- 障碍：`curl (60)` 证书 SAN 不匹配（`CN=5-8lab.com`）；`curl -k` 后仍 `HTTP/1.1 403 Forbidden`（nginx）。两者叠加 ⇒ 拿不到任何内容。
- 解锁条件（任一）：
  1. 站点侧修复——为该域名签发/安装正确证书并把 `chinasugar.org.cn` 绑定到独立 vhost（**不可控，需等待/联系协会**）；
  2. 找到该 IP 上真正承载糖业协会内容的**其他域名或端口**（需人工确认，未验证）；
  3. **换用替代源**：国家统计局 / 农业农村部糖料产量与价格、海关总署食糖进口、泛糖科技等（spec 中若已有替代站，直接切换）。
- 明确不做：不用 `-k` + 伪造 UA 硬闯 403（既无效，也违反不绕过反爬）。

**棉花**
- 无阻塞障碍。唯一约束是**必须走 `http://` 明文 80**；HTTPS 不可用。
- 解锁条件：爬虫配置显式允许明文 HTTP、**禁止自动升级到 https**、关闭 `https_only` 类校验。长期风险：站点若日后整改为强制 HTTPS，需复测。

## 建议

1. **棉花立即接入**：base = `http://www.chinacotton.org/`，列表 `articleList.aspx?sort={1,2,4,5,6}`，详情 `articlePage.aspx?articleID=N`；主通道取 `sort=2`（市场监测，双月）+ `sort=6`（供需平衡表）+ `sort=5`（生产监测）。先把 articlePage 正文结构补测（下一轮可用探测点）。
2. **糖业协会标记 blocked，不派爬虫**：归因为站点 vhost/证书缺陷，与本机网络、代理均无关；代理恢复也**不会**解锁。在 spec 中降级为「需替代源」，并记录 `exit 60 (cert CN=5-8lab.com) + HTTP 403` 作为复现证据。
3. **更正此前的「连接失败」记录**：两站都不是被墙/被拦截；棉是 HTTPS 未部署，糖是证书与 vhost 配置错误。此前若按「需代理」归档，应改为「明文 HTTP 可用（棉）/ 站点侧不可达（糖）」。
4. 顺带发现：`http://www.chinacotton.org/` 首页页脚指向「中国棉花信息网 / 中国棉花网 / 中国棉花协会」三个不同站点，其中**本域名实为「棉花产业经济」研究室站**，与 `chinacotton.org` 名义上的「信息网」主页可能不同——接入前需确认是否要的是这个研究室站。

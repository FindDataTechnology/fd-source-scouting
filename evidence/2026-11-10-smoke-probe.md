# 探针取证实录 · 2026-11-10-smoke

- 时间：2026-11-09T19:23:59.739172+00:00
- 出口形态：直连
- 探针版本：fd-source-probe 0.1.0
- 审计：`/Users/chengsishi/finddata/data-source-scouting/evidence/2026-11-10-smoke-audit.jsonl`

| 目标 | 方法 | 状态码 | 耗时(ms) | 分类 | 出口 | 体前缀(bytes) | 说明 |
|---|---|---|---|---|---|---|---|
| eurostat-hotel-nights | GET | 200 | 1922 | ok(可得) | 2408:8256:328e:2a51:947b:2987:89d4:6c8c | 2048+ | EU27 住宿业月度过夜数（酒店线 E2 同源端点），免 key 直连 |
| mofcom-totalmonth | POST | 200 | 1441 | ok(可得) | 2408:8256:328e:2a51:947b:2987:89d4:6c8c | 2048+ | 商务部数据中心货物进出口月度（侦察簿 W1-K1），免鉴权 POST 表单；需 legacy TLS 档 |
| nbs-easyquery | GET | 403 | 2875 | channel_failure(通道故障) | 2408:8256:328e:2a51:947b:2987:89d4:6c8c | 314 | 国家统计局 easyquery（已知按出口拦截：带浏览器 UA 仍 403，拦截页含 Client IP） |

## 逐条证据（体前缀原样截取，未编辑）

### eurostat-hotel-nights

- URL：`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tour_occ_nim?format=JSON&lang=EN&c_resid=TOTAL&unit=NR&nace_r2=I551-I553&geo=EU27_2020`
- 分类理由：HTTP 200 且内容可读
- 分类注记：—
- 响应头（裁剪）：`content-type=application/json`
- 响应体前缀：

```
{"version":"2.0","class":"dataset","label":"Nights spent at tourist accommodation establishments - monthly data","source":"ESTAT","updated":"2026-11-04T23:00:00+0100","value":{"252":102002788,"253":107557592,"254":126384511,"255":151553673,"256":174339985,"257":244805859,"258":363336991,"259":392477687,"260":225865187,"261":157094023,"262":99049722,"263":102587797,"264":105753778,"265":113616194,"266":128562315,"267":150686105,"268":184891801,"269":235841261,"270":366553819,"271":403669668,"272":229777411,"273":154426395,"274":101843005,"275":105181162,"276":103448956,"277":112671433,"278":138
```

### mofcom-totalmonth

- URL：`https://data.mofcom.gov.cn/datamofcom/front/totalmonth/query`
- 分类理由：HTTP 200 且内容可读
- 分类注记：—
- 响应头（裁剪）：`content-type=application/json;charset=UTF-8`
- 响应体前缀：

```
[[{"imexgap_lj_value":null,"total_value":7608.36,"imexgap_per":null,"type":"月度统计","trade_date":"202609","total_lj_per":null,"import_lj_value":24325.84,"export_per":36.3,"import_lj_per":null,"import_per":31,"imexgap_value":1335.32,"total_lj_value":58032.79,"export_lj_value":33706.96,"export_lj_per":null,"id":"53d8a9efa0a4086201a167a6a81400e0","import_value":3136.52,"imexgap_lj_per":null,"total_per":34.1,"export_value":4471.84},{"imexgap_lj_value":null,"total_value":6837.97,"imexgap_per":null,"type":"月度统计","trade_date":"202608","total_lj_per":null,"import_lj_value":21183.33,"export_per":25,"impo
```

### nbs-easyquery

- URL：`https://data.stats.gov.cn/easyquery.htm?m=QueryData&dbcode=hgnd&rowcode=zb&colcode=sj&wds=%5B%5D&dfwds=%5B%5D`
- 分类理由：HTTP 403（拦截页形态）
- 分类注记：疑似网关/WAF 按出口拦截，非凭据问题；换出口复测而不是申请 key
- 响应头（裁剪）：`content-type=text/html; charset=utf-8`
- 响应体前缀：

```
<!DOCTYPE html>
<html>
<head><title>403 Forbidden</title></head>
<body bgcolor="white">
<center style="margin-top: 100px;"><h1>403 Forbidden</h1></center>
<hr>
<center>Client IP: 2408:8256:328e:2a51:947b:2987:89d4:6c8c</center>
<center>eventID: 1249-1794281040.35-s3zzuc reason:UrlACL</center>
</body>
</html>





```

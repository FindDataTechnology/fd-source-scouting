# data-source-scouting

> **Part of the [Wire line (寻数·柏讯)](https://www.finddatatech.cloud/products/wire) of [FindData](https://www.finddatatech.cloud)** — discovery and evaluation notes for candidate upstream data sources: what a source publishes, how it is reached, and whether it is worth ingesting.

`INDUSTRY-DATA-SOURCES.md` is the working catalogue: one entry per candidate source, with
access path, update cadence, and the reason it was accepted or rejected.

This repository holds **notes and decisions**, not crawler code. The crawlers live in
`fd-industry-data`.

## 目录里有什么

```
INDUSTRY-DATA-SOURCES.md    候选源总账：每源一条，含可访问路径、更新频率、收录/否决理由
agriculture/   (12 篇)      农业垂域侦察报告（chinafeed、customs-agri、fertilizer-pesticide…）
hotel/          (4 篇)      酒店垂域
restaurant/     (4 篇)      餐饮垂域
evidence/                   侦察期的原始取证（响应样本、探针结果）
scripts/                    把侦察结论转成可执行判据的工具
tests/                      上述工具的测试
```

每篇侦察报告的固定结构：**站点、侦察时间与方式、结论**——先给结论再说过程，
因为读的人多数只想知道"这个源能不能用"。

## scripts 做什么

侦察不是一次性的判断，它要能被复核：

| 工具 | 用途 |
|---|---|
| `probe_to_connectivity.py` | 把一次探测结果转成连通性判据 |
| `regression_probe.py` | 对已收录的源重跑探测，发现"以前能访问、现在不能" |
| `extract_candidates.py` | 从页面里抽出候选数据源 |
| `validate_golden.py` | 金标准样本校验 |
| `reconcile_evidence.py` | 侦察结论与取证材料对账 |
| `check_vertical_registry.py` | 垂域登记表一致性 |
| `check_ontology_alignment.py` | 侦察结论与本体对齐 |

## 一份侦察报告长什么样

```bash
# 只做 HTTP 探测，不登录、不绕反爬——报告里的"可达"指公开可访问
python3 scripts/probe_to_connectivity.py <url>
```

结论只有三档：**可采**（能稳定拿到结构化数据）、**需绕**（有反爬，要评估成本）、
**否决**（价值或成本不成立）。否决的源也留在总账里并写明理由，避免下一轮有人
重新调研同一件事。

## License

MIT — 见 `LICENSE`。

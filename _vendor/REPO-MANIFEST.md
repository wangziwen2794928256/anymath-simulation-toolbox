# 外部资源清单（按缺口匹配，逐条校验过存在性）

获取方式：**无需 VPN**，走 `api.github.com/.../zipball`。
脚本：`python _vendor/fetch_repo.py <owner/repo> <目标目录>`
先看清单再拉：`python _vendor/fetch_repo.py <owner/repo> --list`

> ⚠️ 未认证的 GitHub API 有速率限制（60 次/小时），批量校验会被 403 误报。
> 下表"存在性"列已区分"实测存在"与"未校验"。

## A. 必拉（直接填补已定位的缺口）

| # | 仓库 | ★ | 许可 | 体积 | 填补缺口 | 存在性 |
|---|---|---|---|---|---|---|
| A1 | `Imbad0202/academic-research-skills` | 50.4k | **NOASSERTION** | 24 MB | P2+P3：5 个 skill（`academic-paper` 63文件 / `academic-paper-reviewer` 28 / `deep-research` 53 / `sr-screener` 25 / `academic-pipeline` 30）+ `scripts/` 632 + `shared/` 155 | ✅ 实测 |
| A2 | `kourgeorge/arxiv-style` | ~1.4k | MIT | 1.0 MB | P3 顶会风中性壳：arXiv 预印本 LaTeX 模板，**正是你选的 tcolorbox/geometry 重排**的现成基线 | ✅ 曾经实测（MIT/998 KB），后撞速率限制 |

**A1 重要提醒**：许可为 `NOASSERTION`（GitHub 无法识别），**先只做结构分析、不直接并入**，吸收思路后本地重写。

## B. 建议拉（MARL 训练，解决"手写值分解不收敛"）

| # | 仓库 | 许可 | 体积 | 用途 | 存在性 |
|---|---|---|---|---|---|
| B1 | `oxwhirl/epymarl` | Apache-2.0 | ~1 MB | `09-a-track-paper-depth.md` 明确要求用它训 QMIX/MAPPO，**替代手写值分解** | ⚠️ 未校验（速率限制） |
| B2 | `oxwhirl/pymarl` | Apache-2.0 | 283 KB | QMIX 原始实现，论文引用出处 | ✅ 实测 |
| B3 | `Farama-Foundation/PettingZoo` | MIT | 194 MB | 多智能体 Gym 接口 | ⚠️ 未校验 |
| B4 | `Farama-Foundation/Gymnasium` | MIT | — | 单智能体环境底座（EPyMARL 依赖） | ⚠️ 未校验 |

> 体积提示：PettingZoo 194 MB 主要来自测试资源，可用 `--list` 先筛再抓单文件。
> **优先级**：B1 > B2 > B4 > B3。

## C. 可选（有明确价值但非阻塞）

| # | 仓库 | ★ | 许可 | 体积 | 用途 | 存在性 |
|---|---|---|---|---|---|---|
| C1 | `jgm/pandoc` | 40k+ | GPL-2.0 | 72 MB | Markdown→LaTeX/PDF 管道；也可直接用 winget 装 | ✅ 实测 |
| C2 | `synercys/annotated_latex_equations` | ~4k | MIT | 684 KB | 给公式加**注释箭头**的 LaTeX 技法，正好治"公式只有结论式没有推导注释" | ✅ 实测 |
| C3 | `negrinho/deep_architect` | ~1.9k | MIT | 1.9 MB | 架构图的 Python 表达，可作为声明式出图 DSL 的参考实现 | ✅ 实测 |
| C4 | `matplotlib/cheatsheets` | ~4k | BSD-2 | 24 MB | 出图 API 速查（喂给 Agent 减少瞎写） | ✅ 实测 |
| C5 | `dspinellis/latex-advice` | ~1k | NONE | 106 KB | LaTeX 排版最佳实践，补 P3 版式细节 | ✅ 实测（**无许可**，仅阅读） |
| C6 | `Wookai/paper-tips-and-tricks` | ~4k | MIT | 2 MB | 论文图表与表达技巧，补 P3 | ✅ 实测 |
| C7 | `rougier/scientific-visualization-book` | ~4k | NOASSERTION | 290 MB | 科研可视化系统教材（体积大，建议只读不拉） | ✅ 实测 |

## D. 明确跳过

| 仓库 | 理由 |
|---|---|
| `mermaid-js/mermaid`（90.5k★, MIT, 280 MB） | 只是渲染器，不是 skill；引进一个 JS 服务与自动化流水线冲突 |
| `jgraph/drawio`（8.5k★, Apache-2.0, **1.8 GB**） | 桌面 GUI，无法无人值守调用 |
| `mingrammer/diagrams`（42.7k★, MIT） | 需本机 Graphviz（当前未装）；偏云架构图，与仿真流程图匹配度一般。**若 C3 不够用再考虑** |
| `citation-style-language/styles`（84 MB） | 竞赛只需 10–20 篇中文/英文文献，用不上 CSL 全量 |
| `retorquere/zotero-better-bibtex`（410 MB） | 依赖 Zotero 客户端，竞赛场景用不到 |
| `FacebookResearch/Hydra`（379 MB） | 配置管理，对单人流水线是过度工程 |
| `ElegantLaTeX/ElegantPaper`、`mohuangrui/ucasthesis` | 中文学位论文模板，与 A 赛道提交形态不符 |

## E. 拉取建议顺序（一次连通的窗口里按序执行）

```powershell
$py = 'C:\Users\wzw\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$f  = 'D:\anymath-and-simulation\_vendor\fetch_repo.py'

& $py $f Imbad0202/academic-research-skills _vendor/academic-research-skills
& $py $f kourgeorge/arxiv-style            _vendor/arxiv-style
& $py $f oxwhirl/epymarl                   _vendor/epymarl
& $py $f oxwhirl/pymarl                    _vendor/pymarl
& $py $f synercys/annotated_latex_equations _vendor/annotated_latex_equations
& $py $f negrinho/deep_architect           _vendor/deep_architect
& $py $f Wookai/paper-tips-and-tricks      _vendor/paper-tips-and-tricks
& $py $f matplotlib/cheatsheets            _vendor/matplotlib-cheatsheets
```

体积可控（A1 24 MB + A2 1 MB + B1/B2 约 2 MB + C 组约 28 MB ≈ 55 MB），
远小于 D 组任何一个。

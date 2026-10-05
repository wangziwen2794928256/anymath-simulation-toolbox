# _vendor —— 第三方资源（只读引用，勿改上游文件）

本目录存放从外部获取、用于**微调与集成**的开源资源。改动一律落在工作区自己的
`skills/` 里，不直接改这里，便于日后升级。

## 获取通道现状（2026-02 实测，中国网络）

| 通道 | 无 VPN | 有 VPN | 说明 |
|---|---|---|---|
| **`codeload.github.com/<repo>/zip/refs/heads/{main,master}`** | ❌ 超时 | ✅ 通 | **首选**：无需认证、**不限流**，浏览器"Download ZIP"走的就是它 |
| `https://api.github.com` | ✅ 通 | ✅ 通 | 元数据/文件树；**未认证时限流 60 次/小时，批量会 403** |
| `api.github.com/repos/<r>/zipball` | ✅ 通 | ✅ 通 | 无 VPN 时的备选下载通道，但受限流 |
| `https://raw.githubusercontent.com` | ✅ 通 | ✅ 通 | 按路径抓单文件 |
| `https://pypi.org` | ✅ 通 | ✅ 通 | `pip install` 正常 |
| `https://github.com`（网页） | ❌ 超时 | ✅ 通 | 浏览器操作 |
| `https://objects.githubusercontent.com` | ⚠️ 404 | ⚠️ 404 | LFS 大文件可能不可达 |

**结论**：
- **有 VPN 时**用 `codeload` 直连（不限流，最快最稳）；
- **无 VPN 时**用 `api.github.com/.../zipball`（受限流，适合少量仓库）；
- 两条通道都由 `_vendor/fetch_repo.py` **自动降级尝试**，并写入 `PROVENANCE.md`
  记录来源、许可、获取时间。

```bash
python _vendor/fetch_repo.py <owner/repo> _vendor/<name>     # 单仓
python _vendor/fetch_repo.py --batch _vendor/repos.txt --batch-dest _vendor   # 批量
python _vendor/fetch_repo.py <owner/repo> --list             # 列文件树（需 API）
```

## 已获取（第二批，2026-02 补）

| 目录 | 来源 | 许可 | 用途 |
|---|---|---|---|
| `cheatsheets` | `matplotlib/cheatsheets` | BSD-2 | 官方 cheatsheet，画图 API 速查（喂给 Agent 减少瞎写） |
| `matplotlib-cheatsheet` | `rougier/matplotlib-cheatsheet` | BSD-2 | 一页式 matplotlib 精要 |
| `paper-tips-and-tricks` | `Wookai/paper-tips-and-tricks` | MIT | 论文图表与写作技巧 |
| `annotated_latex_equations` | `synercys/annotated_latex_equations` | MIT | **公式加注释箭头的技法**——治"公式只有结论式没有逐步推导" |
| `arxiv-style` | `kourgeorge/arxiv-style` | MIT | arXiv 预印本 LaTeX 模板（P3 版式壳参照） |
| `pymarl` | `oxwhirl/pymarl` | Apache-2.0 | QMIX 原始实现 |
| `epymarl` | **`uoe-agents/epymarl`** | Apache-2.0 | QMIX/MAPPO/IQL 现成实现 + MPE 基准（**替代手写值分解**） |
| `smac` | `oxwhirl/smac` | Apache-2.0 | StarCraft II 多智能体基准 |
| `PettingZoo` | `Farama-Foundation/PettingZoo` | MIT | 多智能体 Gym 接口 |
| `diagrams` | `mingrammer/diagrams` | MIT | Diagram as Code（需另装 Graphviz） |

> **注意**：`oxwhirl/epymarl` 仓库已迁移，正确地址是 **`uoe-agents/epymarl`**。

## 已获取（第一批）

### SciencePlots（MIT）
- 来源：`garrettj403/SciencePlots`，9271★
- 获取方式：`pip install SciencePlots`（PyPI，无需 VPN）
- 安装位置：`<DSH python>/Lib/site-packages/scienceplots/`
- 可用样式（47 个 `.mplstyle`）：
  - 期刊：`nature` `ieee`
  - 配色：`bright` `high-vis` `high-contrast` `light` `muted` `retro` `std-colors` `vibrant` `discrete-rainbow-1..23`
  - 语言/字体：`cjk-sc-font` `cjk-tc-font` `cjk-jp-font` `cjk-kr-font`
  - 杂项：`grid` `no-latex` `pgf` `sans` `latex-sans`
  - 另有 `science` `notebook` `scatter`
- **接入点**：作为 P1 出图底座，替代工作区自研且已停用的
  `skills/csf-simulation-modeling/assets/plotting/nature_style.py`。

### ⚠️ 三个必须绕开的集成坑（已实测，务必照抄下面的配方）

**坑 1：`science`/`nature` 样式会把字体锁成 STIXGeneral → 中文全部变豆腐块 □**
实测 `plt.style.use(['science','nature','cjk-sc-font','no-latex'])` **不生效**：样式
后加载的设置覆盖了前面的字体，渲染结果所有汉字都是空方框。
**必须在样式之后显式接管字体族**，并开启缺字告警（否则静默出豆腐块，肉眼不查就漏）。

**坑 2：`nature` 样式默认 `text.usetex=True` → 本机没有 LaTeX，直接崩**
报错 `RuntimeError: Failed to process string with tex because latex could not be found`。
**离线环境必须叠加 `no-latex`**。

**坑 3：`import scienceplots` 必须在 `plt.style.use(...)` 之前**，否则
`OSError: 'science' is not a valid package style`（样式注册发生在 import 时）。

**验证可用的配方**（本机 SimSun / SimHei / Microsoft YaHei / Noto Sans SC 齐全）：

```python
import matplotlib
matplotlib.use("Agg")
import warnings
import scienceplots                      # 坑 3：先 import 注册样式
import matplotlib as mpl
import matplotlib.pyplot as plt

plt.style.use(["science", "nature", "no-latex"])   # 坑 2：离线必须 no-latex

# 坑 1：样式之后强制接管字体，CJK 放首位
mpl.rcParams["font.family"] = ["sans-serif"]
mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans SC", "DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["mathtext.fontset"] = "dejavusans"

warnings.simplefilter("error", UserWarning)        # 缺字即报错，不静默出豆腐块
```

产出对照：`_stylecheck.png`（**错误示范**，豆腐块）vs
`_stylecheck_fixed.png`（**正确示范**，中文正常）。这两张图建议保留为
P1 视觉 QA 的回归基线。

### LovelyPlots（MIT）
- 来源：`killiansheriff/LovelyPlots`，931★，`api.github.com/zipball` 下载（530 KB）
- 价值：样式表**保留 Adobe Illustrator 可编辑性**（字体不被转曲、图层不合并），
  若后续要人工微调矢量图，这条比 SciencePlots 更合适。
- 目录：`LovelyPlots/lovelyplots/`（Python 包）、`examples/`、`figs/`

## 待定/未获取

| 目标 | 原因 | 是否需要 VPN |
|---|---|---|
| `mingrammer/diagrams`（42.7k★, MIT） | 需本机 Graphviz（未装），且偏云架构图，与仿真流程图匹配度一般 | 否（可 zipball），但价值待评估 |
| `mermaid-js/mermaid`（90.5k★, MIT） | 280 MB，仅用于渲染，属工具而非 skill | 否 |
| `jgraph/drawio`（8.5k★, Apache-2.0） | 1.8 GB 桌面版，与自动化流水线冲突 | 是（体积过大） |
| `Imbad0202/academic-research-skills`（50.4k★, NOASSERTION） | 24 MB / 2844 文件，5 个 skill，重心在学术写作与同行评审，与 A 赛道技术仿真叙事匹配度未验证；**NOASSERTION 许可需先确认** | 否（可 zipball，但建议先看再拉） |

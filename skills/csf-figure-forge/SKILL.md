---
name: csf-figure-forge
description: 顶会顶刊级图表生成与视觉 QA。用于 A 赛道（多智能体复杂系统仿真）及同类仿真/建模论文的图与表：方法总览图（hero figure）、主结果复合组图、主实验大表、消融/排列组合矩阵、场景示意图。提供语义配色单一事实来源、自动撑开的组件库、四个参数化图表原型、渲染→读图审查→修正的视觉闭环、PDF/SVG/PNG 三份导出。也用于诊断"图看起来不够专业"的具体原因（文字溢出、箭头斜穿、配色语义冲突、中文字体缺字、图表标题重复）。
---

# CSF 图表工坊（顶会顶刊级图表）

## 何时使用

- 要画**方法总览图 / hero figure（Figure 1）**：用 `method_figure()`
- 要画**主结果复合组图（a/b/c/d）**：用 `result_panels()`
- 要出**主实验大表 / 对比表 / 消融表**：用 `comparison_table()`
- 要出**消融或排列组合矩阵**：用 `ablation_matrix()`
- 图"看起来不够专业"，需要定位原因并修：走"视觉 QA 闭环"（见下）
- 中文论文里的图出现**豆腐块 □**、下标丢失、文字压线、箭头斜穿

## 三条铁律（都是从实测缺陷换来的）

1. **图内禁止出现标题**。标题只由 LaTeX `\caption{}` 负责。
   实测交付稿里 `图1`/`图5` 的图内已烧入标题、`\caption` 又写一遍，
   **每张图被标注两次**。
2. **语义配色只有一张表**（`csf_fig.SEMANTIC`）。实测同一张复合组图里，
   红色既是"最近出口"（面板 b）又是"静态"（面板 c），自相矛盾。
   `SemanticPalette` 对**未登记的角色直接报错**。
3. **六字以上标签必须换行**，否则必溢出框外（本机 SimHei/Noto 更宽）；
   表题**不要用加粗 CJK**（触发 `TU/SimSun/b/n undefined`，字体回退且行距翻倍）。

## 目录

```
skills/csf-figure-forge/
├── scripts/
│   ├── csf_fig.py          # 底层：样式、语义配色、自动撑开的组件库、三份导出
│   └── csf_archetypes.py   # 原型层：四个参数化图表模板 + 拓扑自检
├── references/
│   ├── topvenue-contracts.md  # 顶会图表与写法契约（含证据来源与反模式）
│   └── ... （见 csf-simulation-modeling/references/12-figure-pipeline.md）
└── examples/
    └── demo_archetypes.py  # 四个原型的可运行示例（也是回归基线）
```

## 快速开始

```python
import sys; sys.path.insert(0, "skills/csf-figure-forge/scripts")
import csf_fig, csf_archetypes as A

# 0) 若题目属于已知五类子问题，先用**方法图模板库**
#    python csf_method_templates.py --list
#    python csf_method_templates.py --make evac_relocation --outdir figures
#    模板：evac_relocation / job_shop / supply_network / epidemic_diffusion / marl_coordination
#    模板只给**结构**（分层+模块语义+连线），把模块名换成你题目的名词即可。

# 1) 建立样式：SciencePlots + 中文字体接管 + 缺字即报错（一次绕开三个集成坑）
csf_fig.use_style("nature", cjk=True, font_size=8.5)

# 2) 方法总览图（Figure 1）——不用模板时手写
A.method_figure(
    lanes=["环境层 Environment", "智能体层 Agent", "算法层 Algorithm", "评估与反馈"],
    nodes=[A.ArchNode("site", "礼堂场地", "24 × 16 m", role="baseline", lane=0, order=0), ...],
    edges=[("cap", "obs", "服务率", "solid"), ("svc", "fb", "队列长度", "dashed")],
    outdir="figures", name="fig1_method", width_mm=A.W_DOUBLE,
)

# 3) 主结果复合组图
A.result_panels(panels, outdir="figures", name="fig2_main", ncols=2)

# 4) 主实验大表（同时产出 .tex + .csv + PDF/SVG/PNG）
A.comparison_table(rows, ["T / s", "Gini", r"$T/T_{\mathrm{lb}}$"],
                   outdir="tables", name="tab_main", caption_key="方法")

# 5) 消融矩阵（自动计算相对基准格的退化百分比）
A.ablation_matrix(M, row_labels=[...], col_labels=[...],
                  outdir="figures", name="fig4_ablation", metric="T / s")
```

## 视觉 QA 闭环（最容易被跳过、也最值钱）

```
1. 出图        → 原型已自动导出 PDF + SVG + PNG(300dpi)
2. 读单图      → 放大检查：文字粘连 / 越界 / 图例压数据 / 配色语义
3. 修正        → 改脚本重出图，再读一次
4. 编译论文    → xelatex（跑两遍稳定交叉引用）
5. 逐页读 PDF  → miktex-pdftoppm -png -r 90 paper.pdf _pdfpages/p，逐页读图
```

**第 5 步不可省**——只有整页才能发现的缺陷：图内标题与 `\caption` 重复、
`\caption` 加粗 CJK 撑开行距、表格三行同值、浮动体错位、公式断裂。

## 自动检查能力

| 能力 | 位置 | 作用 |
|---|---|---|
| 未登记语义角色 | `SemanticPalette.__call__` | 直接 `KeyError`，防配色语义漂移 |
| 同色多角色 | `SemanticPalette.conflict_report()` | 列出同色被多角色占用 |
| 缺字 | `csf_fig.use_style(strict_glyphs=True)` | 缺字即异常，不让豆腐块流出 |
| 模块重叠 / 越界 | `FigSpec.check_overlaps()` / `check_bounds()` | 导出时自动报告 |
| **方法图拓扑反模式** | `ArchSpec.check_topology()` | 跨层横穿 / 同层反向 / 逆层回指用实线 |
| 自动撑开 | `draw_box()` / `ArchSpec` | 按文字长度算宽高，根治溢出框外 |
| 箭头吸附 | `draw_arrow()` / `anchor()` | 锚点吸到框边，根治悬空起点 |
| 正交折线路由 | `ArchSpec.render()` | 跨层连线不斜穿模块 |
| 标签避让 | `ArchSpec.render()` | 候选位择优，不压框、不压其他标签 |
| 图注四段模板 | `references/topvenue-contracts.md` §1.3 | 总述 + 面板说明 + 编码约定 + Best viewed |

## 语言：英文稿一律 `lang="en"`

论文侧已改为**原生英文**（见 `csf-paper-polish`），图必须跟上，否则出现半中半英的稿子。

```bash
python csf_method_templates.py --make all --outdir figures --lang en
python csf_method_templates.py --check-parity     # 中英两版结构是否逐项一致
```

```python
csf_fig.use_style("nature", cjk=False, lang="en", font_size=8.5)
A.method_figure(..., lang="en")
```

`lang="en"` 做三件事：不装 CJK 字体接管、图内固定文案与台账标记用英文、
按 Latin sans 走字体校验。**字体必须校验解析结果**（`verify_fonts=True`）——
静默回退到 DejaVu Sans 是这一类里最常见的缺陷，本仓已多次被它坑过。

### `--check-parity` 治的是"英文版静默失效"

英文标签是**手写的第二份定义**，不是从中文生成的。实测出现过三种失效，全部**不报错**：

| 失效 | 症状 | 怎么被抓住 |
|---|---|---|
| 英文 helper 只调用、**没定义** | 跑 `--lang en` 到第四个模板就 `NameError` | 抛异常 |
| `marl_coordination` **完全没有 lang 分支** | 传 `lang="en"` 得到中文图 | 中英标题相同 |
| 英文版少一个模块 / 改了一层 | 画出来不报错，只是两版图不一样 | 模块数 / lane 对比 |

`check_template_parity()` 对这五种模板做五项比对：层数、模块数、`key`、
`lane/order/role`、边的 `(src,dst,style)`——**只允许文字不同**。
它本身也做过双向验证：把英文分支改成回退中文、删一个模块、挪一个 lane，
三种 mutation 全部被抓出。

> 更根本的教训：`lang` 参数最初只做成了 Python 形参，**命令行没有 `--lang`**。
> 接口存在但不可达，等于不存在，而且没人会去测一条走不到的路。
> 新增能力时必须同时把它暴露到**调用者真正会用的入口**。

## 文字台账 `*.labels.json` / `*.labels.csv`（交付给手工重绘）

图不是最终美术件：标注由你在专业矢量软件里重排。所以每张图都附带
**图内文字台账**，用来在重排后保持措辞、大小写、术语与正文一致。

每行一个文本元素，含：`label_id`、**`svg_id`**（在矢量软件里直接按 id 搜到元素）、
文本内容、`role`（`node`/`lane-label`/`annotation`/`legend`/`tick`/`panel-tag`/…）、
位置（`center_x_pt`/`center_y_pt`、`x_frac`/`y_frac`，坐标系在 `pos_system` 里写明）、
以及图级的 `narrative_role` / `takeaway`。

两项保证：

- **SVG 里文字是真文字**（`svg_fonttype='none'`），不是路径。实测某模板
  `<text>` 38 个、`<path>` 66 个——文字可以直接改字，不用重画。
- **台账记下实际解析到的字体文件**（如 `LibertinusSans-Regular.otf`），
  这样"字体是否真生效"是**可查的证据**，而不是假设。

## 已实测的集成坑（别重犯）

| 坑 | 现象 | 正解 |
|---|---|---|
| `science`/`nature` 锁死字体为 STIXGeneral | 中文全部变 □ | 样式**之后**重置 `font.family`/`font.sans-serif` |
| `nature` 默认 `text.usetex=True` | 无 LaTeX 时直接崩 | 始终叠加 `no-latex` |
| `import scienceplots` 顺序 | 晚于 `plt.style.use` 报 `OSError` | 先 `import scienceplots` |
| `U+207B`（上标减号） | 微软雅黑无此字形 → 报错 | 上标走数学模式 `$^{-1}$` |
| 图例与模块重叠 | 图例落在画布上压住底行 | `ArchSpec` 预留底部专用图例带 |
| 纵横比失衡量被压扁 | 多层面板互相重叠 | 纵横比下限随层数放宽（`aspect_floor`） |
| `states="I"` 单状态 | `epidemic_diffusion` 抛 `NameError` | 已改为直接写边表（原 `for/break` 构造在单状态下从不执行） |

## 与其他 skill 的关系

- 图**画什么**（面板角色、结论、数据源）由 `csf-simulation-modeling` 的
  `references/12-figure-pipeline.md` 的 figure contract 决定；
- 图**怎么画**由本 skill 负责；
- 图的**合规性**（矢量、caption 判据、统计报告）由
  `csf-paper-polish/scripts/csf_readiness.py` 检查；
- 图**题注的措辞**由 `csf-paper-polish/references/english-narrative.md` §7 与
  `csf_prose.py` 的 `S14_CAPTION_DESCRIPTIVE` 管（题注写结论，不写内容）。

# 图表流水线（可执行的出图闭环）

> 本文件替代旧的“图表规范”散文。规范只能**劝阻**，本文件给的是**会报错的工具**。
> 工具位置：`skills/csf-figure-forge/scripts/csf_fig.py`

## 0. 为什么需要“闭环”而不是“规范”

旧版 `06-figures.md` 有 126 行配色/字号规范，但技能里**没有任何动作能让 Agent 看见自己画的图**。
实测后果（`examples/礼堂疏散/figures/`）：

| 图 | 实测缺陷 |
|---|---|
| `AI图1_方法总览.png` | `c(e)=d+λQ` 的下标被吃掉；11 字标题溢出框外；一条红色虚线**斜穿整张图**；蓝色箭头穿过两个框；无面板编号 |
| `AI图2_复合组图.png` | 同一张图里红色既=“最近出口”(b) 又=“静态”(c)；面板 c 用四色任意配色；面板 a 图例盖住曲线；四个面板全无误差棒 |
| `图1_礼堂平面.png` | 图例“人员”压在 y=16 边框上；`E1 1.6m` 叠在星标上；一个点画在场地外 |
| `AI图5_消融与学习.png` | 训练曲线无指标定义/无置信带；面板 d 图例飘在空白处 |
| 整篇 PDF | **图内已烧入标题，`\caption` 又写一遍 → 每张图重复标注两次** |

**结论**：必须把“出图”写成 `渲染 → 读图 → 修正` 的循环，而不是一次性脚本。

## 1. 三个已实测的集成坑（务必照抄配方）

```
坑 1  science/nature 样式把字体锁成 STIXGeneral → 所有中文变豆腐块 □
      plt.style.use(['science','nature','cjk-sc-font','no-latex']) 实测无效
坑 2  nature 样式默认 text.usetex=True → 本机无 LaTeX 直接崩
      RuntimeError: Failed to process string with tex because latex could not be found
坑 3  import scienceplots 必须在 plt.style.use() 之前，否则
      OSError: 'science' is not a valid package style
```

正确配方由 `csf_fig.use_style()` 封装，它做四件事：
1. 先 `import scienceplots`（坑 3）；
2. `plt.style.use(["science", <journal>, "no-latex"])`（坑 2）；
3. **样式之后**重置 `font.family`/`font.sans-serif`，把 CJK 放首位（坑 1）；
4. `warnings.simplefilter("error", UserWarning)` —— **缺字直接报错，不让豆腐块流到交付物**。

```python
import sys; sys.path.insert(0, "skills/csf-figure-forge/scripts")
import csf_fig
csf_fig.use_style("nature", cjk=True, font_size=9.0, strict_glyphs=True)
```

本机字体已确认齐全：`SimSun / SimHei / SimKai / Microsoft YaHei / Noto Sans SC / Times New Roman`。

## 2. figure contract（出图前必填）

`csf_fig.figure_contract_check()` 会校验字段，缺一项就报问题。

这是基础结构检查，不自动证明数据或统计前提正确。只有 `evidence_level` 为 hero/main 时才要求 hero/main 面板；验证/消融/场景图可独立成图。统计口径与不确定性见 [16-evidence-statistics.md](16-evidence-statistics.md)。以下契约仅示范结构，正式数值从真实运行产物生成。

```yaml
conclusion: "比较动态拥塞策略与规则基线的完成时间；结论待真实实验确认"
role_in_paper: "第 6 章主结果"
evidence_level: "hero"          # hero / validation / ablation / sensitivity
integrity_risks:                # 可能被误读的点，必须在正文或 caption 里澄清
  - "启发式结果不代表最优解"
  - "容量下界的假设与可达性必须单独核查"
panels:
  - id: a
    role: hero                  # 仅 hero/main 类型要求主结论面板
    claim: "待实验确认：完成时间差与其区间"
    source: "results/evac_methods.json#/T/summary"   # 数据源 key，供数值冻结
    units: "s"
  - id: b
    role: validation
    claim: "待实验确认：出口流量不均衡度变化"
    source: "results/evac_methods.json#/gini"
    units: "—"
```

## 3. 语义配色：单一事实来源

`SemanticPalette` 把角色名映射到颜色，**未登记的角色直接 KeyError**。这是修掉
“同图内红=基线又=静态”的机制。

| 角色 | 颜色 | 用途 |
|---|---|---|
| `ours` | `#0F4D92` | 本文方法（最高视觉权重） |
| `ours_alt` | `#3775BA` | 本文方法的次要变体 |
| `baseline` / `baseline_2` | `#7F7F7F` / `#B0B0B0` | 基线对照，不抢戏 |
| `bottleneck` | `#D62728` | 瓶颈/告警/最差 |
| `improve` | `#009E73` | 改善方向 |
| `ablation` | `#9A4D8E` | 消融变体 |
| `reference` | `#E69F00` | 参考值/上界/理论值 |
| `highlight` | `#FFD700` | 唯一强调点 |

`pal.conflict_report()` 会列出同色多角色的情况（同色=同义才允许）。

## 4. 组件库：从根上防“文字溢出 / 箭头斜穿”

`FigSpec` 提供三件套：

- `draw_box(x, y, text, role=...)` —— **宽度按最长行自动撑开**（全角按 1.0 em、
  半角按 0.55 em 估算），文字永远不会溢出框外。
- `draw_arrow(src, dst, src_side=..., dst_side=...)` —— 传 `_Box` 时
  **自动吸附到框边锚点**，不再出现 `fig_arch.png` 那种悬空起点。
- `panel_label("a")` —— 面板编号，强制存在。
- `check_overlaps()` / `check_bounds()` —— 导出时自动报告重叠与越界。

## 5. 视觉 QA 闭环（最容易被跳过、也最值钱的一步）

```
1. 出图       → FigSpec.finalize(outdir, name) 导出 PDF + SVG + PNG(300dpi)
2. 读单图     → read_image() 放大检查：文字粘连 / 越界 / 图例压数据 / 配色语义
3. 修正       → 改脚本，重出图，再读一次
4. 编译论文   → xelatex paper.tex（跑两遍稳定交叉引用）
5. 逐页读 PDF → miktex-pdftoppm -png -r 90 paper.pdf _pdfpages/p
                然后逐页 read_image()
```

**第 5 步不可省**——只有整页才能发现的缺陷：

- 图内烧入的标题与 `\caption` 重复（本示例稿每张图都中招）；
- `\caption` 里用加粗 CJK 触发字体回退，把图题行距撑到两倍；
- 表格里三行数值完全相同（426.7 出现三次）在纸面上极其刺眼；
- 浮动体错位、孤行、公式断裂、附录空白页。

### 实测迭代记录（`图1_礼堂平面_重做版`）

同一个脚本，四轮“改‑看‑改”才干净，每轮都是**看图才能发现**的问题：

| 轮次 | 读图发现 | 修法 |
|---|---|---|
| 1 | `E1 1.6m` 标签压住 y 轴刻度 `7.5` | 出口标签从墙外改到**墙内侧** |
| 1 | 容量注释框盖住 E3 出口星标 | 注释从右下角移到右上角室内空白区 |
| 2 | `E3` 标签压住人群点云 | E3 标签移到右下角室内空白区 |
| 3 | `0.8 m` 第二行贴住场地底边框 | y 从 1.05 调到 1.45，留出行距 |

## 6. 五条铁律（都是从实测缺陷换来的）

1. **图内禁止出现标题**。标题交给 LaTeX `\caption{}`。实测交付稿每张图被标注两次。
2. **语义配色只有一张表**，跨面板、跨图全局一致。
3. **按最终尺寸与真实文本边界决定换行**；六字是旧示例的启发式，不是通用长度限制。
4. **表题不要用加粗 CJK**（`\bfseries` 触发 `TU/SimSun/b/n undefined` → 字体回退、
   行距翻倍）。图题同理。
5. **`\caption` 后紧跟 `\label`**，且每张图只承担一个叙事角色；同一图文件被多次引用
   会被门禁判为 `REUSED_FIGURE`。

## 7. 导出与尺寸

- `FigSpec.finalize()` 默认导出 `pdf`（矢量）+ `svg`（可编辑）+ `png`（300 dpi）。
- 尺寸按刊规换算：单栏 89 mm、1.5 栏 120 mm、双栏 183 mm。构造时传
  `width_mm=89/120/183`。
- 嵌入论文时字号 8–9 pt；单独成图 14–16 pt。

## 8. 工具链位置（本机实测可用）

| 工具 | 路径 |
|---|---|
| Python | `C:\Users\wzw\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe` |
| MiKTeX `xelatex` / `latexmk` | `C:\Users\wzw\AppData\Local\Programs\MiKTeX\miktex\bin\x64\` |
| PDF 光栅化 | 同目录 `miktex-pdftoppm.exe` / `miktex-pdfinfo.exe` |
| SciencePlots | `pip install SciencePlots`（47 个 `.mplstyle`，含 `nature`/`ieee`/`cjk-sc-font`） |
| 字体可编辑样式 | `_vendor/LovelyPlots`（保留 Illustrator 可编辑性） |

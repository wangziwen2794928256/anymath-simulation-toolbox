# LaTeX 工程流程（模板 classes 为开源 cumcmthesis，可复用于 CSF/同类国赛）

# LaTeX Project Workflow

## Bundled project

`assets/latex-template/` contains:

- `paper.tex`: a clean starter with the required chapter hierarchy;
- `cumcmthesis.cls`: the user-supplied CUMCM class;
- `figures/`: destination for generated figures, created by the project script.

The class prefers local `simsun.ttc` and `simkai.ttf` files when the user has
legitimate copies in the project directory. When they are absent, it falls back
to the Fandol Chinese fonts bundled with TeX Live. Times New Roman and Arial
likewise fall back to TeX Gyre Termes and TeX Gyre Heros. Do not redistribute
proprietary font files with a generated project.

Create a copy with:

```bash
python3 scripts/create_project.py /absolute/path/to/output-project
```

The command refuses to overwrite an existing nonempty directory.

## Required entry settings

Keep this class line:

```tex
\documentclass[withoutpreface,bwprint]{cumcmthesis}
```

`withoutpreface` removes the commitment and numbering-information pages. `\maketitle` must remain because the class uses it to place the title above the abstract and reset page numbering. Do not add `\tableofcontents`.

The starter raises `secnumdepth` to 4 and defines block-style `\paragraph` headings. This supports the teacher's required hierarchy from `5.1.1.1` through `5.1.1.5`.

## Figures, tables, and equations

- Give every important object a semantic label such as `fig:route-overview`, `tab:parameter-values`, or `eq:objective`.
- Use `\cref{...}` or the project's established cross-reference command.
- Use vector PDF for plots when possible and PNG for raster images. Avoid Chinese characters and spaces in filenames.
- Use booktabs-style three-line tables. Put units in headers and keep numerical precision consistent with the data.
- Define every nonstandard symbol before or immediately after first use and include it in the symbol table when reused.
- Keep captions descriptive enough to understand the object without repeating a full paragraph.

## Appendices

- Use the first `\section` inside `appendices` as Appendix A and place all source code there.
- Keep Appendix A to one or two pages. Remove boilerplate, duplicated utilities, verbose comments, and repeated code, but preserve every statement needed to reproduce the reported results. Keep the listing compact and readable rather than shrinking it into illegibility.
- Use `\subsection{问题一代码}`、`\subsection{问题二代码}` and similar headings inside Appendix A when code needs grouping.
- Use Appendix B and later appendices only for non-code supplements, including extra data, tables, figures, derivations, proofs, questionnaires, parameter descriptions, and intermediate results.
- Do not split code across Appendix A, Appendix B, Appendix C, or Appendix D.
- Do not create Appendix B when no non-code supplement exists.

## Compile and inspect

Prefer:

```bash
latexmk -xelatex paper.tex
```

If `latexmk` is unavailable, run XeLaTeX enough times to resolve references. Inspect the log for undefined references, missing citations, overfull boxes, missing fonts, and missing graphics.

Render the final PDF to images and review every page. Confirm that:

- the first page is the title and abstract, not an information page;
- the abstract ends on page 1;
- the body begins on page 2;
- no table of contents appears;
- floats remain close to their discussion;
- formulas and tables fit within margins;
- headings are neither stranded nor duplicated;
- the abstract through references ends on page 30 when feasible and never exceeds 30 pages;
- the page target is supported by substantive content rather than blank space, repetition, or inflated graphics;
- references appear before appendices;
- Appendix A contains all reproducible code in one or two readable pages;
- Appendix B and later appendices contain only necessary non-code supplementary material.

## 字体与题注（硬性）
- 中文正文用宋体、英文与数字用 Times New Roman（Windows 正式环境）；Mac/TeX Live 编译时自动回退到 Songti SC / FandolSong 与 TeX Gyre Termes。模板已含这段字体配置，不要删改。
- 图题/表题居中、宋体小四、加粗标签；模板用 `\captionsetup{justification=centering, singlelinecheck=false, font={song,minusfour}, labelfont={bf,up}}` 实现。
- 图中字号 ≤ 正文字号（小四/12pt），图片内文字不得大于正文；图内标签、坐标轴、图例统一 8–10pt。
- 图内文字不得互相粘连、不得与数据点/柱体/曲线重叠；生成图时预留边距，图注与轴标签错位。
- 数字与单位之间、图表标题与图之间不出现粘连；导出前逐图放大检查。

## 顶会风中性壳 `csfstyle.sty`（P3 层）

`assets/latex-template/csfstyle.sty` 是**可叠加的 style 包**：保留 `cumcmthesis.cls`
（它带来的中文/西文字体回退链已经实测可用），只在其上重排观感。

为什么不做成新的 documentclass：cls 里的 `\IfFileExists{simkai.ttf}` /
`\setCJKfamilyfont{song}` 等字体配置是踩过坑才对的，换 class 等于把它们推翻重来。

### 它提供什么

| 能力 | 实现 |
|---|---|
| 紧致几何 | `geometry`：A4、四边 22 mm、行距 1.06、段距 0.25em —— 比数模模板信息密度更高 |
| 彩色紧凑标题 | `titlesec`：`\section` 走 `csfOurs`(#0F4D92) 粗体，间距收紧 |
| 页眉页脚 | `fancyhdr`：左章节名（灰）、右页码 |
| 六个顶会风格盒子 | `tcolorbox`：`csfcontrib` / `csfkey` / `csfasm` / `csftake` / `csflimit` / `csfprop` |
| 三线表 | `booktabs` + `\arraystretch{1.15}` |
| 图注/表注 | `caption`：表题在上、图题在下，`labelfont={bf,up}` 只让编号加粗 |
| 算法伪代码 | `algorithm2e`（`ruled,vlined,linesnumbered`），中文输入输出关键字 |
| 语义配色 | 与 `csf-figure-forge/scripts/csf_fig.py` 的 `SEMANTIC` 表**同一套色值** |

### 实测可用的最小前言（照抄）

```tex
\documentclass[withoutpreface,bwprint]{cumcmthesis}
\usepackage{booktabs,graphicx,amsmath,amssymb,float}
\usepackage{csfstyle}

\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{\setmainfont{TeX Gyre Termes}}
% 中文：只设 SimSun + AutoFakeBold，这一条即可消除粗体缺字告警
\IfFontExistsTF{SimSun}{\setCJKmainfont[AutoFakeBold=2.5]{SimSun}}{}
\IfFontExistsTF{SimHei}{\setCJKsansfont{SimHei}}{}

% 必须在文档类设好中文字体之后再调用
\csfsetupcjkbold
```

冒烟测试文件：`assets/latex-template/smoke-csfstyle.tex`（两遍 `xelatex` 均 exit 0、3 页、无 fatal error）。

### 五个已实测的 LaTeX 坑（全部记录在 `csfstyle.sty` 注释里，别重犯）

| # | 现象 | 原因 | 正解 |
|---|---|---|---|
| 1 | `Command \assumption already defined` + calc 级联错误 | 盒子环境名与 `cumcmthesis.cls` 已有命令冲突 | 所有环境**统一加 `csf` 前缀** |
| 2 | `Illegal parameter number in definition of \reserved@a` | `\IfFileExists`/`\IfFontExistsTF`/`\ifcsname` 会把**整个分支**读进来，分支里的 `#1` 被当成外层参数 | 分支内写 `##1`；带参数的 `\newcommand` **提到条件外面** |
| 3 | `TeX capacity exceeded [save size=200000]` | 在 `\AtBeginDocument` 里才 `\let` 旧 `\textbf`，捕获到的是新定义 → **无限递归** | 不要在条件/`\AtBeginDocument` 内捕获待替换的命令 |
| 4 | `The font SimKai cannot be found` + `nullfont` 级联 | fontspec 认不出**族名** `SimKai` | 写**文件名** `simkai.ttf`（cls 就是这么做的） |
| 5 | `Font shape 'TU/SimSun/b/n' undefined`，图题行距被撑到两倍 | SimSun 无粗体字形 | `\setCJKmainfont[AutoFakeBold=2.5]{SimSun}`；**不要**重定义 `\textbf`（见坑 3） |

> 坑 5 的残余：本机仍会打印一条 `Font shape 'TU/SimSun(2)/b/n' undefined` 提示，
> 但粗体渲染已正常（视觉逐页确认）。属良性回退，不阻塞交付。
> 根除需让该 CJK 族本身带 `AutoFakeBold`，属 MiKTeX 字体映射层面，暂不追。

---

# 英文顶会壳 `assets/latex-en/` 的工程流程

## 构建

```bash
python scripts/csf_build.py --tex paper.tex            # 自动选引擎 + 跑够遍数 + 解析日志
python scripts/csf_build.py --tex paper.tex --clean    # 先清中间产物
```

文件：`csfstyle-en.sty`（壳）、`paper-en.tex`（模板，可编译）、`refs.bib`（种子文献）。

**不要用退出码判断成败。** MiKTeX 在"尚未检查更新"时会打印
`major issue: So far, you have not checked for MiKTeX updates.` 并返回 **1**，
而编译完全成功、PDF 正常。`csf_build.py` 因此改用实证判据：
日志里出现 `Output written on` **且**没有 `!` 开头的行。

**引擎必须按语言选。** 英文 → LuaLaTeX：`microtype` 的字体**伸展（expansion）**
只在 LuaTeX 下可用，而伸展是 microtype 收益中更大的那一半；用 XeLaTeX
不报错，只是**静默**失去它，观感变差而无人知道。中文 → XeLaTeX（CJK 字体）。

## 八个已实测的坑（全部记录在 `csfstyle-en.sty` 注释里，别重犯）

| # | 现象 | 原因 | 正解 |
|---|---|---|---|
| 1 | `LaTeX Error: Command \eth already defined` + fatal | `amssymb` 与 `unicode-math` 都定义 AMS 符号 | 用 `unicode-math` 时**不要**加载 `amssymb`（它已覆盖全部 AMS 符号） |
| 2 | `Package microtype Error: The kerning feature only works with pdftex` | `kerning=true` 在 LuaTeX 下直接报错 | 不要开 `microtype` 的 `kerning` |
| 3 | `Missing number, treated as zero` + `Illegal unit of measure`，且报错处 `<to be read again> $` | **把维度寄存器当文本打印**：正文里写 `#1` 而 `#1` 展开为 `\linewidth`。dimen 寄存器在水平模式下非法 | 维度绝不 typeset；占位宏的宽度做成 `[]` 可选参数且不显示，只显示字面量高度 |
| 4 | `\fcolorbox` 比文本块宽 0.8pt → `Overfull \hbox` | 两条 frame rule 各 0.4pt | 宽度用 `\dimexpr#1-2\fboxrule\relax` |
| 5 | 浮动体跑到**论文标题之上** | 第 1 页的 `[t]` 浮动区在标题块上方；官方类靠 `\maketitle` 的执行时机避开，本壳的标题是普通块 | `\csftitle` 末尾加 `\suppressfloats[t]`（真实论文同样如此：第 1 页只有标题/摘要/正文，首个顶浮动体在第 2 页） |
| 6 | `Design rationale..` 出现**两个句点** | `\titleformat{\paragraph}[runin]` 的 after-code 自动加了 `.`，正文里又写了一次 | 去掉自动句点，按 LaTeX 惯例由**作者**写句点（并在行文门禁里查一致性） |
| 7 | **斜体/小型大写静默退化成正体**，编译无任何警告 | 字体集没有声明对应字形（STIX Two 无 slanted），fontspec 静默回退 | 在 `\setmainfont` 里声明 `SlantedFont`/`BoldSlantedFont`；并加 **shape doctor** 在 `\begin{document}` 比对 `\the\font` |
| 8 | `\captionsetup{labelfont={\slshape,\small}}` **完全无效**，题注标签与正文无区别 | caption 宏包的 font-list 值被静默丢弃（同一 option set 里的 `labelsep` 却生效，故不是 option set 没生效） | 改用 `\DeclareCaptionLabelFormat` 写**字面代码**，emphasis/尺寸/分隔符全部自己控制 |
| 9 | `! Package keyval Error: letterpaper,textwidth=5.5in,… undefined`，**且不致命** | geometry 的键解析器**不先展开**参数，直接在 token 层按逗号切分。`\geometry{\csf@geometry}` 因此被当成**一个**键名（`\csname` 会把宏展开进名字里去） | `\expandafter\geometry\expandafter{\csf@geometry}` |
| 10 | 章节标题**压进**上方盒子，横线与盒子底边相交 | 官方 presets 抄来的标题前距是**负数**（NeurIPS `-2.0ex`、ICML `-0.12in`），它是按"前面是段落"调的；前面是 tcolorbox 时没有段距去抵消它 | 盒子自带足够后距：`after skip` 必须**大于**最大负前距（约 8.6pt），取 16pt；8pt 会恰好抵消，缺陷依旧 |

另一个同类坑：`caption` 的 `font=` 键内部要构造 `\csname l@<值>\endcsname`，
所以**值必须是裸名**（`small`、`footnotesize`），写成控制序列 `\small` 会在
`\csname` 里卡住，报 `Missing \endcsname inserted` + `Package caption Error: \small undefined`。
而 `\DeclareCaptionLabelFormat` 的代码是**字面代码**，那里反而必须用控制序列。

### 坑 9 是本轮最危险的一个

它**不报致命错误**、PDF 照常产出、页面看起来也"像那么回事"，但实际上
**所有 preset 尺寸全部被丢弃**，正文回退到 `article` 的默认几何
（letterpaper 上 6.5in，而不是 NeurIPS 的 5.5in）。
壳里一半"让它像目标会议"的东西一直没生效，**而没有任何信号**。

发现方式不是读日志，而是**去量**：写一个只含
`\typeout{GEOMCHECK textwidth=\the\textwidth ...}` 的探针文件，与预期值对照：

```
期望          textwidth=5.5in=397.48499pt   textheight=9in=650.43pt
实测（修后）   397.48499pt / 650.43pt / parindent=0pt / parskip=5.5pt   ✓
```

> **教训：凡是"应该生效"的排版参数，都要有一个把结果打印出来的探针。**
> 日志里没有 `!` 不等于参数生效了。这与 `csf_build.py` 的立场一致：
> 判据要用实测证据（`Output written` + 无 `!`），而不是退出码或"看起来对"。

### 坑 7、8 的排查过程值得记住

这两条都不是"编译报错"，而是**产物与预期不符**，因此只能靠**看图**发现：

- 坑 7 是把 `\textsl{...}` 与 `\textup{...}` 并排、以 260 dpi 裁切对比，发现**逐像素相同**。
- 坑 8 是把题注以 260 dpi 裁切放大，发现标签并未倾斜。

由此得到的工具化经验：

1. **`pdftoppm -png -r 260 -x -y -W -H` 可以直接裁切区域**做高倍局部检查，
   不必整页渲染后再脑补。这是发现"静默外观退化"的常规手段。
2. **门禁必须双向验证。** shape doctor 第一版用
   `\begingroup\edef ...\endgroup`——`\edef` 是局部的，两个宏在 `\endgroup`
   时双双消失，`\ifx` 比较两个未定义宏 → **每个字形都被报为损坏**（包括明显正常的
   `\bfseries`）。一个总是误报的门禁比没有门禁更糟。
   修成 `\xdef` 后，还要构造**必然触发**的反例（把 `BoldFont` 指向 Regular 文件）
   确认它真的会响——只测"正常情况不报"无法区分"正确"与"失效"。
3. 同一逻辑也适用于 `csf_prose.py`：负例（精心写就的英文）必须 **0 命中**，
   正例（中文直译文本）必须命中对应代码。两个方向都测过才敢用。


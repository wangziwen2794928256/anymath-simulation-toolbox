---
name: csf-paper-polish
description: 论文成稿层——以**原生英文**在顶刊顶会美术壳下写作、排版、审校，并在英文定稿后做一次机械化的中文本地化。用于把已有的问题、模型、数据、代码、图表、初稿写成可提交的高质量论文；或检查稿件的论证结构、段落修辞、图表题注、引用、页数与代码附录。不负责建模与算法选型（交给 csf-simulation-modeling）。
---

# 论文成稿层：原生英文写作 · 排版 · 审计（第二层）

本 skill 是工作流的**第二层**，只负责"把已完成的建模成果写成/润色成可提交论文"，与第一层 `csf-simulation-modeling`（建模与算法）分离，避免职责污染。

分层约定：
- `csf-simulation-modeling`：读题、建模范式/算法选型、仿真实验、代码、图表、骨架门禁。
- `csf-paper-polish`（本层）：**语言路线、行文、排版壳、图表叙事角色、终稿审计、本地化**。
- 两层的接口是**已核实的事实**：数值结果、模型、图表、代码。本层绝不编造数据、结果、引文或性能。

## 语言路线：先用原生英文写，最后才翻译

这是本层最重要的一条规则，且有**实证依据**，不是偏好：

旧流程"先用中文写成竞赛论文，再翻成英文"有两个**互相独立**的缺陷，而更大的那个不是翻译：

1. **文档类（主因）。** `cumcmthesis.cls` 是中文竞赛模板：宋体、1.5 倍行距、首行缩进两字符、大留白、"问题重述／基本假设／符号说明"的前置结构。它的**量度（measure）、行距、段式、标题大小写、题注格式、前置结构**全是竞赛味——在那个壳里，英文写得再好也不像顶会论文。
2. **修辞（真实存在，但次之）。** 中文竞赛散文是"总—分—总 + 评价性 + 名词化"的（"有效提升了……具有重要意义"），直译会成体系地产生无主语被动句、`firstly/secondly/finally`、以及无证据的形容词。这不是零散语法错误，而是一组**可枚举、可检测**的模式。

因此：**在目标修辞里直接构建论证**，中文版本作为英文定稿的**机械派生物**，而不是反过来。若论证只以总分总形式存在，译者别无选择只能照搬。

| 阶段 | 语言 | 工具 |
|---|---|---|
| 写作 → 定稿 | 英文（唯一真源） | `assets/latex-en/`、`csf_prose.py`、`csf-build.py` |
| 定稿后（可选） | 中文 / 其他 | `csf_localize.py` + `references/glossary-en-zh.json` |

**未定稿不要翻译。** 英文还在改就翻，两版静默分叉，直到提交前才被发现。

## Start every task

1. 识别题目、年份、可用数据、已完成的模型、已验证的数值结果、图表、代码与要求的交付物。
2. 区分"已核实事实"与"计划中的工作"。不编造数据、结果、引文、模型性能或敏感性结论；未决事项标注 `TODO`。
3. **起草任何一段正文之前，先读 [references/english-narrative.md](references/english-narrative.md)**——它是本层的行文契约：摘要五个动作、引言五段漏斗、相关工作按对比组织、方法必带设计理由、实验七步、题注写结论、对冲梯度、以及十三条中译英失效模式及改写。
4. 创建/编译/修复 LaTeX 工程前读 [references/latex-workflow.md](references/latex-workflow.md)；选版式前读 [references/venue-style-specs.md](references/venue-style-specs.md)（**官方 .sty 实测参数表**，含 13 条 UNVERIFIED 标注）。
5. 中文版本任务（本地化、中文终稿审计）另读 [references/writing-style.md](references/writing-style.md) 与 [references/teacher-requirements.md](references/teacher-requirements.md)。

## 英文顶会壳 `csfstyle-en.sty`

`assets/latex-en/csfstyle-en.sty` 是**中性英文顶会壳**，与中文壳解耦。用法：

```latex
\documentclass[10pt]{article}              % icml/aaai/aamas 需加 twocolumn
\usepackage[neurips,stix,final]{csfstyle-en}
```

选项：`venue` = `neurips`(默认) | `icml` | `aaai` | `aamas` | `nature` | `elsevier`；
`fonts` = `stix`(默认) | `times` | `libertinus` | `charter`；
`draft`（行号 + 显示 claim/evidence 标记）、`print`（黑色链接）、`boxes`（浅底盒子）。

**参数出处（可复查，不要凭记忆改）**：`neurips`/`icml`/`aaai` 三套的每个数值都抄自官方 style 文件，
文件已 vendored 在 `_vendor/venue-styles/`，代码注释里逐条标了行号。`aamas` 是 acmart/sigconf 近似
（官方 2025 套件被 Cloudflare 403，无法取得）；`nature`/`elsevier` 是**风格化**实现（这两家不发布通用 LaTeX 类）。

实测得到、且**猜不出来**的几条：

| 事实 | 出处 | 为什么重要 |
|---|---|---|
| NeurIPS 2025 是**单栏**（5.5in × 9in） | `neurips_2025.sty:117-124` | 与"顶会都是双栏"的直觉相反 |
| ICML 2025 / AAAI 2025 是**双栏** | `icml2025.sty:326`、`aaai25.sty:41` | 量度差距很大：6.75in vs 7.0in |
| NeurIPS 与 ICML 都用**块状段落**（`\parindent 0pt` + 5.5/6pt 段距） | `neurips_2025.sty:228-229`、`icml2025.sty:659-664` | 一种不并排看就发现不了的风格签名 |
| **AAAI 却缩进**（`\parindent 10pt`、段距 2pt） | `aaai25.sty:147,185` | 不要为了"统一"把它改平——差异是真实的 |
| **AAAI 标题居中且不编号**（`secnumdepth=0`） | `aaai25.sty:163-173` | 强制编号会立刻不像 AAAI |
| ICML 子子节用**小型大写**（`\sc`）而非斜体 | `icml2025.sty:645-646` | 一个字符级细节就区分出 ICML 风 |
| NeurIPS 标题被 4pt／1pt 两条横线夹住 | `neurips_2025.sty:290-332` | 最易识别的视觉签名，已复现 |

壳里另有三个为**本工作流**而设的构件：

- `\csfclaim{C3}{…}\csfevi{fig:main,tab:main}`——把"主张↔证据"绑定写进**源码**，`draft` 模式可见、`final` 模式消失。`csf_prose.py` 在两种模式下都能静态校验（`S15_CLAIM_NO_EVIDENCE`）。治的是"有图但没有任何一句话需要它"。
- `\csffigplaceholder[宽]{高}`——按**成图尺寸**占位并承载题注。因为你会在专业软件里重画矢量图，所以图未完成时版面、页数、题注长度就必须定下来，否则图一落地页面就变、正文要重写。
- `\csf@checkshape` shape doctor——`\begin{document}` 时比较每个字形选择的**字体标识**是否与正体相同，相同即告警。这条是被真事故逼出来的：STIX Two 没有 slanted 字形，`\slshape` 静默退化成正体，编译无警告、PDF 里却少了一个斜体，只能靠 260 dpi 逐像素比对才发现。

## Choose the operation

- 新建工程：`python scripts/create_project.py OUTPUT_DIR`，或直接复制 `assets/latex-en/`（含 `paper-en.tex`、`refs.bib`，可编译）。
- 用户已有工程时直接在其内工作，保留其文档类、宏、参考文献体系、图与无关改动。
- 用户只给部分草稿时只改所请求的章节，并核对相邻章节的术语与符号一致性。
- 编译：**用 `csf_build.py`，不要直接调 lualatex**。原因是退出码不可信：MiKTeX 在"未检查更新"时会打印 `major issue` 并返回 **1**，而编译其实完全成功；直接看 `$LASTEXITCODE` 会把每次成功构建都判成失败，同时掩盖真正的 `!` 错误。该脚本按**实证判据**判断成功（日志里有 `Output written on` 且无 `!` 行），并按语言自动选引擎：英文 → LuaLaTeX（`microtype` 字体**伸展**只在 LuaTeX 下可用，而伸展是 microtype 收益中更大的一半；XeLaTeX 会静默禁用），中文 → XeLaTeX。

```bash
python scripts/csf_build.py --tex paper.tex            # 自动选引擎，跑够遍数含 BibTeX
python scripts/csf_build.py --tex paper.tex --clean
```

## Build the paper from evidence

1. 写正文前先建"证据台账"：把每个问题映射到输入、假设、模型、求解器、输出、检验、图表、表格与引文。
2. 每个重要量只有一个规范名与符号，正文、公式、图、表、代码统一复用。
3. 先写含真实方法与证据的方法／结果章，再由已完成的技术路线倒推引言，摘要最后写。
4. 每个结果都可追溯到一次计算、一张表、一张图或一个给定事实；有精确数值和单位就用上。
5. **数字、单位、符号不得在本地化或润色中改变**——`csf_localize.py` 对数字与引用做集合级严格对拍。

## 图表只承担两件事：位置与叙事

图不是最终美术件：它**占定版面**，并承载读者必须带走的那句话。矢量重绘与标注由你手工完成。由此有三条硬约束：

1. **题注写结论，不写内容。** `csf_prose.py` 的 `S14_CAPTION_DESCRIPTIVE` 会报"以 shows/illustrates/depicts 开头且无结论动词"的题注。
   - ✗ Figure 3 shows the architecture of the proposed method.
   - ✓ Two capacity constraints bind at different λ; the switch between them is what limits throughput (Sec. 5.3).
2. **每张图一个叙事角色。** 同一个图文件被两个不同角色复用，是"图表复用塌陷"，`csf_gate.py` 会失败。
3. **交付标签清单。** 标注要手工重排，所以图导出时附带机器可读的文本清单（内容、角色、位置），保证重排后措辞、大小写、术语仍与正文一致。

## Final gate

**第一步：行文门禁 `csf_prose.py`**（英文学术散文，四类检查：转译折损 / 夸大表述 / 结构动作 / LaTeX 机制）

```bash
python scripts/csf_prose.py --tex paper.tex
python scripts/csf_prose.py --tex paper.tex --min-severity WARN
```

实测标定（**双向验证过**，这是它能被信任的原因）：对一段精心写就的顶会风英文——0 ERROR / 0 WARN；
对一段典型"中文直译"文本——18 ERROR / 20 WARN，且命中项与问题一一对应。

| 类别 | 代表检查码 | 治什么 |
|---|---|---|
| T 转译折损 | `T01_FIRSTLY` `T03_WELL_KNOWN` `T04_IMPORTANT_ROLE` `T05_RAPID_DEVELOPMENT` `T06_MAINLY` `T08_NOMINALIZATION` `T10_THROUGH_CAN` `T14_VERY` `T09_LONG_SENTENCE` | 首先/其次/最后、众所周知、具有重要意义、近年来随着…快速发展、本文主要、进行…分析、通过…我们可以、程度副词、长句 |
| H 夸大表述 | `H01_SIGNIFICANT` `H03_NOVEL` `H04_SUPERLATIVE` `H05_BELIEVE` `H06_PROVE_CAUSAL` | `significant` 无检验（最常被审稿人具体反对）、`novel` 自我评价、无限定最高级、用信念代替证据、从相关推因果 |
| S 结构动作 | `S01_ABSTRACT_LEN` `S10_RELATED_NO_CONTRAST` `S11_NO_LIMITATIONS` `S13_NO_FAILURE_CASE` `S15_CLAIM_NO_EVIDENCE` | 摘要 4–6 句（ICML 2025）、相关工作无对比、缺局限章、不报失效区间、主张无证据 |
| M LaTeX 机制 | `M01_BARE_PERCENT` `M02_CN_PUNCT` `M03_NUMBER_RANGE` `M04_ETAL` | **裸 `%` 吞掉整行且编译不报错**、全角标点、区间用单连字符、`et al` 不规范 |

**第二步：骨架与就绪度门禁 + 人工复核**

1. 同时运行 `csf-simulation-modeling/scripts/csf_gate.py`、`csf_readiness.py` 与 `csf_prose.py`，解决所有 ERROR。
2. 就绪度门禁的检查码与顶会依据（**每条都有官方文件或论文原文出处**）：

| 检查码 | 依据 |
|---|---|
| `NO_GAP_SENTENCE` / `NO_NUMBER_IN_ABSTRACT` | 顶会摘要固定功能位；NeurIPS CFP 禁止无信息量摘要 |
| `ABSTRACT_TOO_LONG` / `TOO_SHORT` | ICML 2025 官方：ideally 4-6 sentences |
| `NO_ASSUMPTIONS_SECTION` | AAMAS 2025 §1.2 Assumptions of interest |
| `NO_LIMITATIONS_SECTION` | NeurIPS Paper Checklist #2 |
| `NO_DISPERSION` / `DISPERSION_UNDERSPECIFIED` / `ERRBAR_SYMMETRY_UNCHECKED` | NeurIPS Checklist #7：写明 variability 来源与是 std 还是 sem |
| `NO_SEEDS` / `FEW_SEEDS_CI_WARNING` | 顶会实测 3/6/10/20 种子；rliable 指出 3 runs 时 bootstrap CI 低估覆盖 |
| `PVALUE_ONLY` | rliable (NeurIPS 2021)：避免 p 值二分法，改用区间估计 + 效应量 |
| `NO_COMPUTE_REPORT` | NeurIPS Checklist #8；AAMAS 2025 把报训练时长列为评估缺陷 |
| `BASELINE_COVERAGE` / `BASELINE_GAP` / `BASELINE_BUDGET_UNSTATED` | 顶会基线四类族谱；MAPPO §4.1 调参预算等价 |
| `BOLD_CRITERION_MISSING` | MAPPO 表注：within 1 standard deviation of the maximum |
| `NA_UNDOCUMENTED` / `NO_FAIRNESS_NOTE` | MAPPO：用预训练的方法须声明不做直接比较 |
| `NO_ODD` | JASSS ODD Protocol 2020（ABM/仿真类近硬要求） |
| `RASTER_FIGURES` | ICML 2025：折线/柱状图尽量用矢量 |

3. 确认每个问题都有模型建立（含逐步推导）、求解、结论、验证或敏感性分析、失效区间；篇幅用推导与对比实验支撑，不注水。
4. 确认参考文献全部真实可查、全部被引用；`refs.bib` 里的条目字段**必须逐条核对**——仓库里的种子文献是真实工作，但卷期页码是尽力而为，未经核对即视为缺陷。
5. **逐页视觉检查最终 PDF**。排版事故只在像素上暴露：本轮就是靠渲染 PNG 逐页看，才发现浮动体跑到标题之上、run-in 标题出现两个句点、以及斜体形状静默退化。

## 本地化（英文定稿之后）

```bash
python scripts/csf_localize.py --freeze --en paper.tex      # 冻结英文真源
python scripts/csf_localize.py --check  --en paper.tex --zh paper-zh.tex
```

对拍判据分两类，与 `csf_parity.py`（Python↔Julia）同一思路：
**永远算错的**——数字集合、引用键、label、图表公式计数、claim/evidence 集合；
**允许不同的**——语序、冠词、连接词。
并检测"半翻译"（中文里残留 3 个以上连续英文词）与术语表里的**禁用译法**。

## 交付形态

- 从第一版初稿起就输出可编译的 `paper.tex`（英文壳），不交付纯 Word/Markdown 稿。
- 每次修改都同步更新 `.tex`，保证"文字版 = 代码版 = PDF 版"三者一致。
- 中文版是英文定稿的派生物，**不是**并行维护的第二真源。

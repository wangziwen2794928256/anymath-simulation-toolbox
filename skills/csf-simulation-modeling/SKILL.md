---
name: csf-simulation-modeling
description: 2026全国大学生仿真建模应用挑战赛（A赛道多智能体复杂系统仿真，兼容B/C）专用工作流。用于本赛事的建模范式与算法选型、仿真实验设计与复现、代码可读性规范、竞赛论文写作，以及赛后扩展成Q2-Q4 SCI/会议论文。不用于与本赛事无关的通用数学建模。
---

# CSF 仿真建模（2026 挑战赛 · A 赛道）

面向：3 人 AI 队，官方环境 AnyMath；本地 Mac 写 Python，回传 Windows/AnyMath 运行。

## 何时使用
- 建模选型、算法实现、仿真实验设计、代码整理与复现
- 写竞赛论文与演示视频
- 赛后把作品扩展成 Q2–Q4 SCI 或会议论文

## 一条贯穿始终的原则
**从第一天起就按“可发表论文”的水平做：保留 baseline、随机种子、超参、源码、结果指标，全部可复现。**
竞赛论文只是这篇论文的第一版，不是终点。这样赛后投稿时只需“补实验 + 重排版”，而不是推倒重来。

## 语言路线：正文用**原生英文**写（先读这条）

论文不再"先写中文再翻译"。理由有实证依据，不是偏好：旧流程的两个缺陷中，
**更大的那个不是翻译，而是文档类**——`cumcmthesis.cls` 的量度、行距、段式、
标题大小写、题注格式、"问题重述/符号说明"前置结构全是竞赛味，英文写得再好也不像顶会论文。
次之才是修辞折损（中文"总—分—总 + 评价性"直译成无主语被动句 + firstly/secondly）。

因此：**论证在目标修辞里直接构建**，英文是唯一真源，中文版是定稿后的机械派生物。

| 环节 | 用什么 |
|---|---|
| 版式壳 | `csf-paper-polish/assets/latex-en/csfstyle-en.sty`（6 个 venue preset，参数抄自官方 .sty） |
| 行文契约 | `csf-paper-polish/references/english-narrative.md`（摘要五动作、引言五段漏斗、十三章失效模式） |
| 编译 | `csf-paper-polish/scripts/csf_build.py`（英文走 LuaLaTeX，中文走 XeLaTeX；**不看退出码**） |
| 行文门禁 | `csf-paper-polish/scripts/csf_prose.py` |
| 图（英文） | `csf_method_templates.py --lang en` + 标签台账 `labels.json` |
| 本地化 | 英文定稿后才跑 `csf-paper-polish/scripts/csf_localize.py` |

本层的每个门禁都要加 `--lang en`（或依赖自动判定）：骨架配额在英文下按
**prose word** 计，中文下仍按非空行数计，两条路径互不影响。

## 硬性门禁（不通过不许交付）

规范写在 markdown 里只能“劝阻”，所以本技能配了**六个会报错的门禁**，不通过不许进入下一阶段。

| 门禁 | 脚本 | 管什么 |
|---|---|---|
| 机理卡 | `csf_mechanism.py` | 现象 → 机制（为什么） |
| **方法选型** | **`csf_select.py`** | **问题 → 方法（用什么）** |
| 骨架/数值 | `csf_gate.py --lang {zh,en}` | 章节配额、数值冻结、引用一致性 |
| 论证链 | `csf_narrative.py` | 图表与论断是否互补（防图漂） |
| **AnyMath 可移植** | **`csf_interop.py`** | **代码能否在平台上跑** |
| **跨语言对拍** | **`csf_parity.py`** | **Python ↔ Julia/AnyMath 数值是否等价** |

（行文层另有两个门禁 `csf_prose.py` / `csf_localize.py`，归 `csf-paper-polish` 管。）

### 门禁零：机理卡 + 方法选型（P2，拿了赛题第一件事）

**在写任何结构之前**，先做两步：**查机制**（为什么）与**选方法**（用什么）。

```bash
# 1) 机制：现象指纹 → 机理卡
python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint 拥堵 排队 出口
python skills/csf-simulation-modeling/scripts/csf_mechanism.py --show MECH-01
python skills/csf-simulation-modeling/scripts/csf_mechanism.py --check   # 18 张卡 / 78 文献 key

# 2) 方法：问题指纹 → 候选方法 + 分层行动方案（**推荐加 --plan**）
python skills/csf-simulation-modeling/scripts/csf_select.py --fingerprint 排队 服务台 随机到达 --plan
python skills/csf-simulation-modeling/scripts/csf_select.py --pick DES CTDE IQL
python skills/csf-simulation-modeling/scripts/csf_select.py --check      # 23 个方法 / 10 条规则
```

**分工**：`mechanisms.json` 回答「**为什么**会发生」（现象→机制→可证伪预测）；
`methods.json` 回答「**该用什么**」（问题→方法→复杂度/数据/落地库/校验/踩坑）。
两者通过 `mechanisms` 字段挂钩——**写论文时每个方法都要接到机制上**，否则只是套方法。

`--plan` 按 **基线 → 上界/下界 → 诊断 → 主方法 → 消融** 分五步给出推进顺序，
并做**基线族谱自查**（顶会要求 ≥3 类：规则/启发式、精确/上界、MARL 代表、近两年 SOTA）。

### 门禁零·补：机理卡库明细

**在写任何结构之前**，先提取题目与数据的「现象指纹」，到机理库里查卡：

库里 18 张卡（`references/mechanisms.json`，人类可读版 `references/13-mechanism-cards.md`），
每张卡强制七要素：**现象指纹 → 一句话机制 → 数学形式 → 可证伪的可算预测 → 建模选择 →
最小实验 → 反模式**。

| 领域 | 卡片 |
|---|---|
| 通用 | MECH-02 容量下界 · MECH-03 Lagrangian 对偶与影子价格 · MECH-04 排队闭合估计 · MECH-09 无政府价格 PoA · MECH-11 牛鞭效应 · MECH-13 公共随机数 CRN · MECH-15 校准可辨识性 · MECH-17 鲁棒性最坏情形 · MECH-18 VV&A 三层校验 |
| 疏散 | MECH-01 拥堵外部性/Pigou 定价 · MECH-10 社会力与基本图 · MECH-16 距离-拥堵权衡与异质性 |
| 调度 | MECH-05 分派规则交换论证最优性 · MECH-14 前瞻收益递减 |
| 多智能体 | MECH-06 对称性破缺 · MECH-07 IGM 与值分解边界 · MECH-08 CTDE 与信用分配 |
| 传染病 | MECH-12 基本再生数与阈值行为 |

**硬规则**：`failable_prediction` 就是你的可证伪假设 H1..Hn（它天生带可检验判据，不是
“范围限定式”装饰）；`cite` 里的出处写进参考文献；**`--check` 会强制校验卡里引用的
文献 key 必须真实存在于 `05-literature.md`，从机制上杜绝虚构文献**。
若无卡片匹配你的指纹，**应新增卡片而非硬套**。

### 门禁一：骨架与数值（P0）

```bash
python skills/csf-simulation-modeling/scripts/csf_gate.py <paper.tex> \
       [--figures-dir DIR] [--results results/*.json]
```
退出码 0=通过 / 1=有 ERROR / 2=有 WARN。它把六类“实测踩过的坑”变成可执行检查：

| 检查码 | 抓什么 | 为什么必须有 |
|---|---|---|
| `MISSING_SECTION` / `SECTION_TOO_THIN` | 章节缺失、章节低于行数下限 | 实测 18 页标准下，形式化章只写了 8 行 |
| `TOO_FEW_FIGURES` / `TOO_FEW_TABLES` | 图 <5、表 <4 | 实测只剩 3 图 2 表 |
| `MAS_INCOMPLETE` | 形式化缺 (S,A,P,O,R)/拓扑/信用分配/宏观量 | 缺要素 = 不像仿真科学论文 |
| `IDENTICAL_TABLE_ROWS` | 表里多行数值完全相同 | 实测三行同为 426.7，等同编造 |
| `UNCONVERGED_WITH_NUMBERS` | 报“未收敛”却填了具体指标 | 实测 Q 学习行填了 0/0/400 |
| `ORPHAN_FIGURES` / `DANGLING_REF` / `REUSED_FIGURE` | 孤儿图、断引用、一图多角色 | 实测 28 张图未进正文 |
| `UNFROZEN_NUMBER` | 正文数值在 `results/*.json` 里找不到来源 | 数值冻结，杜绝占位数字 |
| `NUMBER_REPEATED` / `AI_CLICHE` | 同一数值反复出现、套话超阈值 | 提示可能是模板化/注水 |

### 门禁二：图表视觉闭环（P1）

**渲染 → 读图审查 → 修正，必须真跑一轮**，不允许“写完画图脚本就当图没问题”。

```python
import sys; sys.path.insert(0, "skills/csf-figure-forge/scripts")
import csf_fig
csf_fig.use_style("nature", cjk=True, font_size=9.0)   # 中文字体接管 + 缺字即报错
pal = csf_fig.SemanticPalette()                        # 语义配色，未登记角色直接报错
```
- 每张图**先写 `figure_contract`**：结论 / 面板角色 / 数据源 key / 单位 / 证据层级 / 可能被误读点。
  `csf_fig.figure_contract_check()` 会校验必填字段，缺 hero 面板或缺 integrity_risks 直接报错。
- 导出一律三份：**PDF（矢量）+ SVG（可编辑）+ PNG（300dpi）**，由 `FigSpec.finalize()` 保证。
- 产出后必须**逐图放大读图**，再**逐页读编译出的 PDF**（用 `miktex-pdftoppm` 光栅化）。
  只读单图会漏掉“图题重复”“表题撑行距”“三行同值”这类只有整页才看得见的缺陷。

## 工作流（按阶段）
-1. **先产出科学推理链**（拿到赛题第一件事）：现象→问题本质→机制→可证伪假设 H1..Hn→为假设选模型→递进实验→解释成败。读 `references/11-scientific-reasoning.md`。推理链未定，不许排结构。
0. **再产出论文蓝图**（拿到赛题第一件事）：宏观模型 + 章节蓝图 + 图表蓝图 + 内容量 → 读 `references/00-paper-blueprint.md`，并按其中模板写出蓝图，确认“文章分几个方向、几个章节、每章解决什么、每张图表对应哪段结论”之后，才进入建模。
1. 读题拆解：明确 KPI、决策变量、约束、数据 → 在 `notebooks/` 做 EDA。
2. 选建模范式与算法 → 先按 `references/08-domain-playbook.md` 归类领域、取标准模型与真实参数做基线，再按 `references/00-paper-blueprint.md` 的“建模三问”给问题建数学形式，最后查 `references/07-methods-library.md` 选方法（禁止无理由套用）。
3. 搭规则版 MVP 跑通 → 再加优化/RL → 形成“基线 vs 创新点”对照。
4. 实验与复现 → 按 `references/02-code-standards.md` 组织代码、种子、日志、结果，结果存 `results/*.json`（供数值冻结门禁用）。
5. **写图**：先 figure contract，再按 `references/12-figure-pipeline.md` 出图，跑视觉闭环。
6. 写论文 → **用英文顶会壳直接写**（见上面「语言路线」）；中文版是定稿后的派生物，不并行维护。
7. **过门禁**：`csf_gate.py --lang en` 与 `csf_prose.py` 均无 ERROR 才可交付；
   编译统一走 `csf_build.py`（它按语言自动选引擎、跑够遍数，并**按实证判据而非退出码**判成功），
   再用 `pdftoppm` 逐页渲染验收——整页级缺陷（浮动体错位、标点重复、字形静默退化）只有看图才能发现。

## 资源路由
- **机理卡片库（拿到赛题最先做）**：`references/mechanisms.json` + `13-mechanism-cards.md`，用 `scripts/csf_mechanism.py` 按现象指纹查卡。**先查卡，再写推理链**。
- 科学推理链（写推理链时对照）：`references/11-scientific-reasoning.md`（现象→机制→假设→选模型→递进实验→解释成败）
- 领域作战手册（拿到赛题先对号入座）：`references/08-domain-playbook.md`（人群疏散/物流调度/供应链/传染病/多智能体协同 五大领域的标准模型+关键方程+真实参数+验证基准+图型叙事套路）
- 论文蓝图（拿到赛题先做）：`references/00-paper-blueprint.md`（宏观模型 + 章节/图表蓝图 + 内容量 + 建模三问）
- 选模型/算法：`references/01-methodology.md`（范式/校验/现代方法）+ `references/07-methods-library.md`（本问题类方法总库 + 选型决策矩阵 + 反模式）
- 写代码/跑实验：`references/02-code-standards.md`（含指标库 + 算法分层 + 训练工程；代码骨架 `assets/code-template/`，MARL 训练脚本 `assets/code-template/train_marl.py`）
- 图表/表格/公式范式：**先读 `references/12-figure-pipeline.md`**（可执行的出图闭环：contract → 底座 → 视觉 QA → 双导出；三个已实测的 SciencePlots/CJK 集成坑）与 `references/10-ai-conference-style.md`（AI 顶会工业风）；配色细则另见 `math-modeling-contest` skill 的 Nature 指南。工作区 `assets/plotting/nature_style.py` 已停用。
- 查文献：`references/05-literature.md`（BibTeX 就绪，按类取用）
- 写论文：**先读 `references/09-a-track-paper-depth.md`**（A 题=多智能体协同/仿真研究，18 页深度标准，纠正数模化薄模板）；再按 `references/03-competition-paper.md` 与模板 `assets/paper-templates/competition-paper.md`
- 赛后发论文：`references/04-journal-extension.md`（模板 `assets/paper-templates/journal-paper.tex`）

## 图表铁律
所有图走 `csf-figure-forge`（见 `references/12-figure-pipeline.md` 与上面的 P1 门禁）：先写 figure contract（一图一结论 + 面板 map + 证据层级 + 数据源 key），再按其语义配色与 CJK 字体规则绘制，矢量+300dpi 双份。

**五条从实测缺陷里换来的铁律**：
1. **图内禁止出现标题**。实测交付稿里，`图1`/`图5` 的图内已烧入“图 1 方法总览…”，而 `\caption` 又在图下写了同样一句，**每张图都被重复标注两次**。标题只由 LaTeX `\caption{}` 负责。
2. **语义配色只有一张表**。实测同一张复合组图里，红色既是“最近出口”（面板 b）又是“静态”（面板 c），自相矛盾。用 `SemanticPalette`，未登记角色直接报错。
3. **六字以上标签必须换行**，否则要么溢出框外（10–12 字必溢），要么交叠相邻元素。
4. **表题不要用加粗 CJK**。实测 `\caption` 里的 `\bfseries` 触发 `Font shape 'TU/SimSun/b/n' undefined`，xelatex 回退字体并把行距撑到两倍。
5. **`\caption` 之后的 `\label` 必须紧跟**。实测 `\caption{}\label{fig:formal}` 被后续 `\ref{fig:formal}` 指向了错误的浮动体，导致正文把“场景图”当“算法流程图”引用。

## 关键约束（别犯）
- AnyMath 原生支持 `ipynb`(Python)、`jl`/`ngscript`(Julia)、EngeeModel 物理建模语言；**首选 Python**，迁移成本最低。
- 全文 AIGC 比例、总相似比超标直接取消资格；论文必须自己实质性修改。
- 指导教师不得参与实质求解；不得跨校组队、一人多队。
- 视频占 30%；评委先看摘要和结果，再看模型和数据。

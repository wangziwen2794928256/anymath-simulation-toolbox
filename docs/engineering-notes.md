> 这份笔记面向**维护者**，记录每个设计决策背后的实测证据，以及被反例推翻过的第一版做法。
> 它的价值在于：同样的坑不要再踩第二次。面向使用者的说明见根目录 [README.md](../README.md)。

> **开源发布时的清理（记录在案）**：以下内容已在发布前移除，笔记里若仍有引用属**历史记录**——
> `archive/早期工作站/`；`reference/papers/`（含一篇 CUMCM 获奖论文 PDF，1.7 MB）；`reference/analysis/`；
> `examples/{2018B-RGV, 2025A-流水车间, comparison-RGV, _scaffold-demo}`（合计约 2 MB，均属通用数模竞赛，
> 与本仓库 A 赛道多智能体仿真这一主题无关）；`p5.svg`；`docs/win-mac差异.md`；
> 以及 `examples/礼堂疏散/figures/` 中 34 个被后续版本取代的图（只保留正文实际引用的 3 张）。
> 理由：它们是**迭代遗弃物**，保留会让读者分不清哪个才是当前样貌。

# 工程笔记（设计决策 · 踩过的坑 · 验收判据）

## 一、目标
为「2026 第二届全国大学生仿真建模应用挑战赛 · A 赛道（多智能体复杂系统仿真）」打造一套专用 skill，使 AI 能端到端产出**交付级**论文（建模→仿真→图→LaTeX→PDF）。当前由另一智能体继续优化。

## 二、三个 skill 与调用方式
已安装到 `~/.codex/skills/`（同名目录在工作区也有留档）。

| Skill | 职责 | 何时调用 | 典型说法 |
|---|---|---|---|
| `csf-simulation-modeling` | 本赛事专用：**机理卡匹配**、科学推理链、建模选型、仿真实验、图、论文蓝图、**P0 门禁** | 拿到赛题先查机理卡 → 推理链+蓝图 → 建模 | “用 csf-simulation-modeling 先给这道题的科学推理链和论文蓝图” |
| `csf-figure-forge` | **出图闭环**（P1）：语义配色、自动撑开的组件库、视觉 QA、矢量+300dpi 三份导出 | 每次画图 | “按 csf_fig 出图并做视觉审查” |
| `csf-paper-polish` | 中文论文润色、**顶会叙事壳**、**`csfstyle.sty` 版式壳**、LaTeX 排版、终稿审计 | 已有建模结果后润色成文 | “用 csf-paper-polish 把结果润色成 paper.tex + PDF” |
| `math-modeling-contest` | 通用数模流水线（G1-G6 门禁、DOCX/PDF、Nature 图） | 需要通用数模能力或对照时 | “用 math-modeling-contest 处理这道数模题” |

**推荐调用链（P0→P4 重构后）**：
```
csf_mechanism 查机理卡 → 11号推理链 → 00号蓝图 → 建模+仿真（结果存 results/*.json）
→ csf_fig 出图 + 视觉 QA → csf-paper-polish 叙事+版式 → csf_gate 过门禁 → 编译逐页验收
```

## 二·补、可执行门禁（不通过不许交付）

### 语言路线（这就是本轮最大的一次改动，先读这条）

**原生英文写作，最后才翻译。** 旧流程"先写中文竞赛论文再翻成英文"有两个独立缺陷，
更大的那个不是翻译，而是**文档类**：`cumcmthesis.cls` 的量度、行距、段式、
标题大小写、题注格式、"问题重述/符号说明"前置结构全是竞赛味，英文写得再好也不像顶会论文。
次之才是修辞（中文"总—分—总 + 评价性"直译成无主语被动句 + firstly/secondly）。
所以论证必须**在目标修辞里直接构建**，中文版只是英文定稿的机械派生物。

| 门禁 | 命令 | 作用 |
|---|---|---|
| 行文 | `python skills/csf-paper-polish/scripts/csf_prose.py --tex paper.tex` | 四类检查（转译折损 T / 夸大表述 H / 结构动作 S / LaTeX 机制 M）。**双向标定过**：好英文 0 命中，中文直译 18 ERROR |
| 编译 | `python skills/csf-paper-polish/scripts/csf_build.py --tex paper.tex` | 按语言自动选引擎（英文 LuaLaTeX / 中文 XeLaTeX），跑够遍数 + BibTeX；**按实证判据判成功，不看退出码** |
| 机理卡 | `python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint <现象>` | 18 张机理卡；`--check` 校验卡引用的文献 key 真实存在 |
| 骨架/数值 | `csf_gate.py --tex paper.tex --lang {zh,en}` | 章节配额、图表配额、MAS 要素、孤儿图、断引用、重复行、数值冻结。**`--lang en` 后配额按 prose word 计**，中文路径行为逐字未变（已 diff 验证 10 ERROR/5 WARN 不变） |
| 就绪度 | `csf_readiness.py --tex paper.tex --lang en` | 顶会合同：种子/离散度/基线族谱/局限章/计算量/矢量图。英文正文长度按词计（旧版按汉字计，英文稿恒为 0） |
| 方法选型 | `csf_select.py --plan` | 23 方法 / 10 规则，五步推进 |
| 跨语言对拍 | `csf_parity.py` | Python↔Julia 数值对拍（确定性策略必须完全一致） |
| 中英对拍 | `csf_localize.py` | 数字/引用/label/图表计数/claim 集合严格相等；只允许语序冠词不同 |
| 图 | `csf_method_templates.py --make all --lang en` | 五领域方法图英文模板；`--check-parity` 校验中英两版结构逐项一致 |
| 视觉闭环 | `csf_fig.use_style(...)` + `read_image` 逐图 + `pdftoppm` 逐页 | 渲染→读图→修正；单图与整页两级验收 |

### 本轮通过"渲染成像素再看"发现的缺陷（日志里全是 0 错误）

这部分是本轮最有价值的经验：**没有 `!` 不等于参数生效了**。

| # | 症状 | 根因 | 判据 |
|---|---|---|---|
| 1 | 斜体/小型大写**静默退化成正体** | 字体集未声明 slanted 字形 | 260 dpi 裁切对比 `\textsl` 与 `\textup` **逐像素相同** |
| 2 | 题注标签样式**完全无效** | caption 宏包静默丢弃 `labelfont` 的字体列表（同 option set 的 `labelsep` 却生效） | 改用 `\DeclareCaptionLabelFormat` 写字面代码 |
| 3 | **所有 preset 尺寸被丢弃**，正文回退到 article 默认 6.5in | geometry 的键解析器**不先展开**参数，`\geometry{\csf@geometry}` 被当成一个键名 | 写 `\typeout{textwidth=...}` 探针**去量**：修后 397.48499pt = 5.5in |
| 4 | 浮动体跑到**论文标题之上** | 第 1 页顶浮动区在标题块上方 | `\csftitle` 末尾 `\suppressfloats[t]` |
| 5 | 章节标题**压进**上方盒子 | 官方标题前距是负数（NeurIPS −2.0ex），按"前面是段落"调的 | 盒子 `after skip` 必须大于最大负前距（取 16pt；8pt 恰好抵消） |
| 6 | `Design rationale..` 两个句点 | run-in 标题 after-code 自动加句点 | 去掉自动句点，由作者写 |

> 排查手段固定下来：`pdftoppm -png -r 260 -x -y -W -H` 直接**裁切局部**高倍看；
> 以及给"应该生效"的参数写**打印探针**。

## 三、csf-simulation-modeling 的参考文件（按优先级）
- `references/mechanisms.json`（+ `13-mechanism-cards.md`）：**机理卡片库（P2）**，18 张卡，每张含「现象指纹→机制→数学形式→可证伪的可算预测→建模选择→最小实验→反模式→出处」——**先于一切**
- `references/11-scientific-reasoning.md`：科学推理链（现象→本质→机制→可证伪假设→为假设选模型→递进实验→解释成败）
- `references/12-figure-pipeline.md`：**图表闭环（P1）**，含三个 SciencePlots/CJK 集成坑与五条铁律
- `references/00-paper-blueprint.md`：论文蓝图（宏观模型+章节/图表蓝图+内容量）
- `references/10-ai-conference-style.md`：AI 顶会图表范式
- `references/08-domain-playbook.md`：A 题五领域标准模型+真实参数
- `references/07-methods-library.md`：方法总库+选型矩阵
- `references/09-a-track-paper-depth.md`：18 页深度标准（其配额已由 `csf_gate.py` 强制）
- 其余 01-06：建模范式、代码规范、论文评分、期刊扩展、文献库（含 J 节机理库出处）


## 四、目录结构（已重构，按 skills/examples/reference/archive 分区）
```
skills/                      # 3 个 skill
examples/                    # 自包含示例：礼堂疏散/ 2018B-RGV/ 2025A-流水车间/ comparison-RGV
  └── <name>/code/           #   各示例的仿真/实验代码与数据 json
reference/                   # papers/ + analysis/(skill对比分析、框架叙事示例)
docs/                        # win/mac 差异等
archive/早期工作站/           # 已废弃的 01-04 骨架
```

## 五、实验代码与数据（关键）
**此前所有仿真/实验代码都在 /tmp，不在工作区。本次已收拢到 `实验代码/`：**
- 疏散仿真：`evac_sim.py`（核心 run()）、`evac_deep.py`（密度/速度）、`evac_ablation.py`（频率/λ 消融）、`evac_methods.py`（6 方法对比）
- RGV 调度：`rgv3.py`（多步前瞻，得 366/281/375）、`rgv_sim.py`/`rgv2.py`（贪心）
- 学习式：`dqn_exit.py`（线性 Q）、`climbing.py`（Climbing Game IQL vs QMIX）、`vdn_*.py`/`qmix_mpe.py`（值分解尝试，未收敛）
- 图脚本：`fig*.py`/`ai_figs.py`/`rgv_figs.py`/`evac_figs*.py`
- 数据：`evac_*.json`、`dqn_results.json`、`climbing.json`、`rgv_results.json` 等

**已知问题（如实交代）**：
1. `vdn_iql.py/vdn_fast.py/vdn2.py/qmix_mpe.py` 手写值分解**未收敛**（同质共享策略无法破对称性）。正确做法用 EPyMARL/PyMARLzoo+，勿手写。
2. RGV 组 2 效率仅 76%（RGV 关键路径瓶颈，属真实结果，非 bug）。
3. 图脚本依赖 /tmp 的 json，已一并收拢，运行前确认路径。
4. **`evac_methods.json` 里 `nearest` / `shortest_queue` / `static_cong` 三者数值完全相同**——
   经查是**数学必然**（t=0 时队列全为 0，二者都退化为最近出口），不是 bug。
   但论文 `tab:main` 把它们当三次独立评测并列，属**呈现层面的诚信问题**，必须改写（见第七节 P4 待办）。

## 六、当前状态与下一步
- 已完成：三层 skill、科学推理链(11号)、AI图表范式(10号)、领域手册(08号)、两篇示例稿（疏散 11页/0TODO、RGV 7页/前瞻95%）。
- 用户判定：当前输出“仍不如直接用 nature skills”，需要更强建模能力。

### P0→P4 重构进度（本轮完成 P0/P1/P2/P3 + 工具链）

| 阶段 | 状态 | 交付物 |
|---|---|---|
| **P0** 可执行门禁 | ✅ | `csf-simulation-modeling/scripts/csf_gate.py`；实测示例稿 **10 ERROR + 5 WARN**，全部命中真实缺陷 |
| **P1** 图表闭环 | ✅ | `csf-figure-forge/scripts/csf_fig.py`（语义配色/自动撑开组件库/三份导出）+ `references/12-figure-pipeline.md`；示例图 1 重做，**4 轮看图迭代修掉 5 个缺陷** |
| **P2** 机理卡片库 | ✅ | `references/mechanisms.json`（18 卡）+ `scripts/csf_mechanism.py`（查/校验/生成 md）+ `13-mechanism-cards.md`；`--check` 通过（78 文献 key 全部可查） |
| **P3** 版式壳 + 叙事壳 | ✅ | `csf-paper-polish/assets/latex-template/csfstyle.sty`（6 个语义盒子，冒烟测试两遍 exit 0）+ `references/conference-narrative.md`（摘要七句式、相关工作方法族表） |
| **工具链** | ✅ | MiKTeX 用户级安装；`xelatex` 实测编译示例稿 → **11 页**（A 赛道标准 18 页）；`miktex-pdftoppm` 逐页读图打通 |
| **P4** 示例稿重构 | ⏳ 待办 | 见下 |

### 本轮通过"逐页读 PDF"发现的**整页级缺陷**（单图审查看不到）
1. **图题重复**：`图1`/`图5` 的图内已烧入标题，`\caption` 又写一遍 → 每张图被标注两次；
2. **表题加粗触发字体回退**：`Font shape 'TU/SimSun/b/n' undefined`，图题行距被撑到两倍；
3. **实测 11 页 vs 标准 18 页**：门禁"内容量不足"的结论被物理证实；
4. **表 2 三行同值**在纸面上极其刺眼。

### 赛题与平台事实（2026-02 核实）

| 项 | 内容 | 来源 |
|---|---|---|
| 主办 | 中国仿真学会（全国一级学会）+ 吉林财经大学 | 赛事公告 |
| 技术支持 | 北京格瑞纳电子（**AnyMath**），设 AnyMath 专项奖金（卓越/创新/菁英/新锐 4000/3000/2000/1000 元） | 赛事公告 |
| 竞赛时间 | **2026-10-16 20:00 → 10-20 20:00（4 天）** | 赛事公告 |
| A 赛道定位 | 多智能体协同演化、复杂动态系统仿真；面向**群体性、网络化、调度型**复杂系统，做数字化建模、动态推演与优化，**挖掘复杂系统运行机理** | 赛道说明 |
| 提交内容 | 模型构建 + 仿真推演 + **方案设计** + 成果报告（+ 支撑材料含完整可运行源码与环境说明） | 赛事公告 |
| 平台语言 | AnyMath 文档站 `engee.com/helpcenter`；基础语言为 **Julia（`jl`/`ngscript`）**，亦支持 `ipynb`；有"代码生成"与"综合语言"章节 | AnyMath 文档 |

### 本轮（第 2 轮）新增能力：图表原型库 + 顶会规范门禁

| 交付物 | 作用 |
|---|---|
| `skills/csf-figure-forge/scripts/csf_archetypes.py` | **四个参数化图表原型**：`method_figure`（方法总览图）/ `result_panels`（复合组图）/ `comparison_table`（主实验大表，同时产出 .tex+.csv+三份图）/ `ablation_matrix`（消融矩阵，自动算相对基准的退化%） |
| `skills/csf-figure-forge/SKILL.md` | 出图工坊入口：三条铁律、视觉 QA 五步闭环、六类已实测集成坑 |
| `skills/csf-figure-forge/references/topvenue-contracts.md` | **顶会图表与写法契约**（每条附证据来源与 URL）+ 20 条反模式 + 28 条可勾选清单 |
| `skills/csf-paper-polish/scripts/csf_readiness.py` | **顶会就绪度门禁**：摘要缺口句/数字、ICML 4–6 句、独立假设与局限章、误差棒语义、种子数、算力、baseline 四类族谱、加粗判据、N/A 标注、公平性隔离、ODD、矢量图 |
| `_vendor/fetch_repo.py` | 多通道（codeload → api zipball → raw）自动降级的仓库获取工具，带 `PROVENANCE.md` 溯源 |
| `_vendor/{cheatsheets, paper-tips-and-tricks, annotated_latex_equations, arxiv-style, pymarl, epymarl, smac, PettingZoo, diagrams}` | 出图/公式注释/LaTeX 模板/MARL 训练框架 |

**原型库的自动检查能力**（都是实测缺陷换来的）：未登记语义角色直接报错、
缺字即异常（不让豆腐块流出）、模块重叠/越界检测、**方法图拓扑反模式自检**
（跨层横穿 / 同层反向 / 逆层回指用实线）、按文字长度自动撑开、箭头锚点吸附框边、
**跨层正交折线路由**（不斜穿模块）、箭头标签候选位避让。

### P4 待办（下一轮，注意赛期将近）

1. **按 18 页预算补全示例稿骨架**，直到 `csf_gate.py` 通过——但**不要为示例稿抠细节**，
   示例稿只用来验证 skill 的约束能力。相关骨架文件已备好：
   `examples/礼堂疏散/paper/sec1-front.tex`、`sec3-formalization.tex`、`sec4-model.tex`、`sec5-exp.tex`。
2. **`eval_methods_fixed.py` 已修正两处实质错误**（静态策略等价性、标准 Gini 定义），
   数值以 `code/results/sweeps.json` 为唯一来源；正文数值需按该文件同步。
3. **用 EPyMARL 真训 QMIX/MAPPO** 补学习式协同（`_vendor/epymarl` 已就位）；
   在此之前不得编造协同结果。
4. **AnyMath 落地**：等 AnyMath 文档子代理的报告（`anythmath` 平台能力与 Python→Julia 移植风险表），
   据此写"本地 Python 验证 → AnyMath 复现"的迁移清单。

---

## 七、本轮（第 3 轮）交付：原生英文路线

用户的判断是"汉语论文与英文顶会顶刊在转译过程中的折损使外观很差"。
**这个判断一半对**：外观差的主因是文档类（见 §二·补），修辞折损是真实但次之的第二层。
本轮把两层都按构造解决。

### 新增/改造的文件

| 文件 | 性质 | 说明 |
|---|---|---|
| `skills/csf-paper-polish/assets/latex-en/csfstyle-en.sty` | 新增 49 KB | 中性英文顶会壳，6 个 venue preset + 4 套字体；**neurips/icml/aaai 的每个数值都抄自官方 .sty 并标了行号** |
| `skills/csf-paper-polish/assets/latex-en/paper-en.tex` | 新增 | 可编译英文模板（4 页），按顶会论证顺序编排，含 `\csfclaim`/`\csfevi`/`\csffigplaceholder` |
| `skills/csf-paper-polish/assets/latex-en/refs.bib` | 新增 | 6 条真实种子文献（**卷期页码需逐条核对后才可用**） |
| `skills/csf-paper-polish/assets/latex-en/showcase/*.png` | 新增 | 单栏(NeurIPS)/双栏(ICML) 两个 preset 的渲染基线 |
| `skills/csf-paper-polish/scripts/csf_prose.py` | 新增 44 KB | 行文门禁，四类 40+ 条规则，**每条都给改写** |
| `skills/csf-paper-polish/scripts/csf_build.py` | 新增 | 编译驱动，按实证判据判成功 |
| `skills/csf-paper-polish/scripts/csf_localize.py` | 新增 | 中文定稿后的机械本地化对拍 |
| `skills/csf-paper-polish/references/english-narrative.md` | 新增 | 行文契约：五段漏斗、摘要五动作、十三条中译英失效模式及改写 |
| `skills/csf-paper-polish/references/venue-style-specs.md` | 新增 43 KB | 子代理从**官方 .sty** 提取的参数表（13 条 UNVERIFIED 标注） |
| `skills/csf-paper-polish/references/latex-workflow.md` | 扩写 | 新增英文壳流程 + 坑 6–10 |
| `skills/csf-paper-polish/SKILL.md` | 重写 | 语言路线升为第一原则 |
| `skills/csf-figure-forge/scripts/*.py` | 改造 | `lang="en"`；标签台账 `labels.json`；`--check-parity` |
| `skills/csf-figure-forge/examples/templates-en/` | 新增 | 五领域英文方法图 + 台账 |
| `skills/csf-simulation-modeling/scripts/csf_gate.py`、`csf_readiness.py` | 改造 | `--lang {zh,en}`，中文路径逐字未变 |
| `_vendor/venue-styles/` | 新增 | NeurIPS/ICML/AAAI/ACM/IEEE 官方 style 文件（`fetch_styles.py` 可重跑） |

### 明确的能力边界（不要夸大）

- `nature`/`elsevier` 两个 preset 是**风格化**实现，不是官方类（这两家不发布通用 LaTeX 类）；
  `aamas` 是 acmart/sigconf 近似（官方 2025 套件被 Cloudflare 403）。
- 壳是**写作工具**，不是合规检查。真投稿要用 `_vendor/venue-styles/` 里的官方类
  （AAAI 的类会对 16 个宏包直接 `\PackageError`，包括 `geometry` 与 `hyperref`）。
- `csf_prose.py` 的 S 类只做**能可靠判断**的子集；冠词缺失、单复数一致等**故意不检测**
  （不可靠的门禁会被关掉），列在 `english-narrative.md` §10。
- 图的视觉细节（个别标注压线、层标签轻微裁切）**有意未打磨**——按用户要求，
  图只负责位置与叙事，矢量重绘与标注由手工完成；台账就是为这一步准备的。

### 下一步

1. **赛前压测**：用 skill 完整走一道全新 A 赛道题（查卡 → 选方法 → 骨架 → 英文成稿 → 对拍），计时并记录卡点。
2. 用 `csf_localize.py` 走一遍中英对拍，验证冻结/对拍链路。
3. `_vendor/epymarl` 真训 QMIX/MAPPO 后，才允许写学习式协同结果。
4. AnyMath 免费许可"每月 20 小时"且原文排除科学研究用途 → **参赛前必须向主办方确认许可适用性**。

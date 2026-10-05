# 顶会顶刊图表与写法契约（可执行版）

> 本文件的每一条都对应 `scripts/` 下的**会报错的检查**，或 `csf_archetypes.py` 里的
> **原型实现**。规范的正文引用了本次实际检索到的顶会官方文件与论文原文（见每节"依据"），
> 目的是让"像不像顶会论文"从主观判断变成可核对的契约。
>
> 两个门禁：
> - `csf-simulation-modeling/scripts/csf_gate.py` —— 骨架与数值诚信
> - `csf-paper-polish/scripts/csf_readiness.py` —— 写作规范契约（本文件第 4–7 节）
>
> 出图原型：`csf-figure-forge/scripts/csf_archetypes.py`（本文件第 1–3 节）

---

## 0. 先看一张总表：哪些是硬约束，哪些是惯例

| 项 | 性质 | 依据强度 | 检查方式 |
|---|---|---|---|
| 摘要含"缺口句" | **硬**（缺则动机不清） | 顶会摘要实测共同结构 | `csf_readiness` → `NO_GAP_SENTENCE` |
| 摘要含具体数字 | **硬** | NeurIPS CFP 禁止无信息量摘要 | `NO_NUMBER_IN_ABSTRACT` |
| 摘要 4–6 句 | 建议 | ICML 2025 官方原文 "ideally 4-6 sentences" | `ABSTRACT_TOO_LONG/SHORT` |
| 独立的假设章节 | **硬** | AAMAS 2025 §1.2 "Assumptions of interest" | `NO_ASSUMPTIONS_SECTION` |
| 独立的局限章节 | **硬** | NeurIPS Checklist #2 建议独立 Limitations 节 | `NO_LIMITATIONS_SECTION` |
| 误差棒写清 std/sem 与算法 | **硬** | NeurIPS Checklist #7 | `DISPERSION_UNDERSPECIFIED` |
| 报告 seeds 数与取值方式 | **硬** | 顶会实测 3/6/10/20 | `NO_SEEDS` |
| 报告算力 | **硬** | NeurIPS Checklist #8 | `NO_COMPUTE_REPORT` |
| baseline ≥3 类 | **硬** | 顶会基线族谱实测 | `BASELINE_COVERAGE` |
| 加粗判据写进 caption | **硬** | MAPPO 表注原文 | `BOLD_CRITERION_MISSING` |
| 折线/柱状图用矢量 | 建议 | ICML 2025 官方原文 | `RASTER_FIGURES` |
| ODD 协议 | 建议（ABM 类近硬） | JASSS ODD 2020 | `NO_ODD` |
| 图内不写标题 | **硬（本工作实测）** | 交付稿每图标题重复两次 | 人工/视觉 QA |
| 虚线=反馈、实线=数据流 | 惯例（有单例证据） | CROSS 图注显式声明 | 原型自动加图例 |

---

## 1. 方法总览图（hero figure / Figure 1）

### 1.1 四种合法形态，按题目语义选

| 形态 | 何时用 | 真实例子 |
|---|---|---|
| **概念对照图** | 题目有强现实语义（疏散、调度、治理） | HaSD Figure 1：红机器人=不理想行为、蓝=对齐后行为 |
| **多层架构图** | 有清晰的"环境→智能体→算法"分层 | QMIX Figure 2：`(c) 单元结构 → (a) 子模块 → (b) 端到端` |
| **数据流/编解码图** | 方法是序列/表示学习 | Sable Figure 2：编码器→隐藏态→解码器，图注直接写张量名 |
| **visual ODD** | ABM/仿真类论文（**本赛道最该抄**） | ODD Protocol 2020 Figure 3：`Initialization → Submodels → Analyses` |

> **依据**：[QMIX (ICML 2018)](https://ar5iv.labs.arxiv.org/html/1803.11485)、
> [HaSD](https://arxiv.org/html/2501.17431v1)、
> [Sable](https://ar5iv.labs.arxiv.org/html/2410.01706)、
> [ODD Protocol 2020 (JASSS 23(2) 7)](https://www.jasss.org/23/2/7.html)

### 1.2 结构规则（`method_figure()` 已内建）

1. **层数 2–3 层**（本工作原型支持到 4 层，但顶会证据里未见过 5 层以上的成功总览图）。
2. **必须同时出现三类块**：`本地策略` + `仅训练期使用的集中模块` + `数据流载体`
   （replay buffer / 轨迹数据集 / 队列状态）。
   依据：[Hierarchical Cooperative MARL with Skill Discovery](https://ar5iv.labs.arxiv.org/html/1912.03558)
3. **颜色承担功能分组**，不是装饰。在 caption 里逐字声明：
   `In red are the hypernetworks … shown in blue`（QMIX 原文）。
4. **虚线语义必须在 caption 里定义**。目前找到的唯一显式声明来自 CROSS 图注：
   "the dotted arrows form a part of the internal perception (update) processes"
   → 即**虚线 = 内部/训练期通路，实线 = 执行期主数据流**。
   本工作原型采用该约定并**自动生成图例**。
5. **正文必须逐面板点名**（`Figure 2b demonstrates …`），不能只写一次总引用。
   依据：[EMC (NeurIPS 2022)](https://ar5iv.labs.arxiv.org/html/2111.11032)
6. **拓扑自检**：`ArchSpec.check_topology()` 会拒绝三类反模式——
   跨层横穿（横向跨位远大于纵向层差）、同层反向、逆层回指用实线。
   这是本工作补充的机制：顶会论文没有公开这条规则，但"图看不懂"几乎都源于它。

### 1.3 图注模板（四段骨架，`csf_archetypes` 的 `caption_template()` 可直接生成）

```
[总述句]     Figure N: Overview of <方法名>, our <一句话定位>.
[面板/方位]  (a) <子模块>; (b) <端到端流程>; (c) <单元结构>.
             或：At the top …, At the bottom …（上下分支结构）
[编码约定]   Solid arrows denote the execution-time data flow;
             dashed arrows denote the feedback loop / training-only path.
             Red marks the bottleneck; blue marks the proposed method.
[可选]       Best viewed in colour.
```

**反模式**：只写一句 `Overview of our approach` 却给了 4 个面板 6 条箭头——
读者无法判断这不是拼贴。

---

## 2. 复合结果组图（multi-panel figure）

### 2.1 三条最强范式（都有原文证据）

1. **同指标跨环境 → 横向并排，共享 y 轴语义，caption 只写一次总述**
   （MAPPO Figure 1 "Performance of different algorithms in the MPEs."）
2. **首图三面板 = 性能 / 效率 / 规模，每个面板的 caption 自带结论 + 数字**
   （Sable Figure 1：`Left: ranks best in 34/45 tasks`、`Middle: 6.5× throughput`、`Right: scales to thousands of agents`）
   —— **这是"只读 caption 也能拿到全部结论"的极强范式，本赛道应直接抄。**
3. **同一样本的三个切面共用一条时间轴**（机制可解释性三连图）
   （CROSS Figures 5–7：行为选择 → 目标支配度 → 行为效用）
   —— 对"证明仿真模型不是黑箱"极有用。

### 2.2 面板标签的三种合法形式

`(a)(b)(c)` / `a) b)` / `Left·Middle·Right` / `At the top·At the bottom`。
**"必须放左上角、必须某字号"未获证据**——本工作原型统一用左上角粗体，是工程选择而非规范。

### 2.3 工程约束（`result_panels()` 已内建）

- 跨面板**统一配色字典**（同一 role 同一颜色），图例只在第一个面板出现（共享图例）。
  依据：[rliable README](https://raw.githubusercontent.com/aai-institute/rliable/master/README.md) 的
  `colors=dict(zip(algorithms, sns.color_palette('colorblind')))` 与独立 legend 图做法。
- 每个面板一句 `claim`（面板结论）写在面板上方，替代"读图靠猜"。
- 折线/柱状图导出**矢量**（见第 6 节）。

---

## 3. 科研表格：主实验大表与消融矩阵

### 3.1 主表朝向：**行 = 环境/场景，列 = 算法**（顶会主流）

证据：MAPPO Table 1（行=22 个 SMAC map，列=7 个方法）、Table 2（行=6 个 GRF 场景）、
AAMAS 2025 benchmark 主表（行=任务，列=算法）。
**反向朝向**（行=算法）仅在"环境少、算法多"时合理。

### 3.2 四点值报告的必要信息（缺一项即为不完整）

| 必须写清 | 为什么 |
|---|---|
| 离散度是 **std** 还是 **sem** | NeurIPS Checklist #7 明文要求 |
| 跨几个 **seeds** | 顶会实测：MAPPO 用 6/10、Melting Pot 用 3、仿真类交通控制用 20 |
| 每个 seed 内部**如何取一个标量** | MAPPO：每轮 32 局评估胜率 → 取最后 10 次评估的**中位数** |
| 是否含**未报告的失败实验** | NeurIPS Checklist #8 |

### 3.3 最优/次优的排版：**bold + underline，且判据必须写出来**

MAPPO 表注原文（最值得抄的一条）：
> "We **bold** all values within 1 standard deviation of the maximum…"

**"最优 = 落在最大值 1 个标准差内的所有值"比"最优 = 单个最大值"稳健得多**，
尤其在多种子下。本工作的 `comparison_table()` 已实现 bold（最优）/ italic（次优），
并在生成的 `.tex` 里提示需把判据写进 caption。

### 3.4 公平性分组必须隔离

用了预训练 / 额外数据 / 更多预算的方法必须单列并声明
`does not constitute a direct comparison`（MAPPO 对 TiKick 的处理）。
未报告的格子用 `/` 或 `—`（MAPPO 用 `/`）。

### 3.5 跨任务聚合：IQM + 分层 bootstrap CI + 性能剖面

**原始出处**：Agarwal et al., *Deep RL at the Edge of the Statistical Precipice*,
**NeurIPS 2021 Outstanding Paper**, arXiv:2108.13264。
其 Table 1 的官方建议：

| 目标 | 不推荐 | 推荐 |
|---|---|---|
| 聚合性能的不确定性 | 点估计 | **分层 bootstrap 置信区间** |
| 跨任务性能的变异性 | 每任务 mean 的表格 | **performance profile**（分数分布） |
| 汇总指标 | mean（被离群任务主导）/ median（半数任务为 0 也不变） | **IQM**（四分位均值），另报 **probability of improvement** 与 **optimality gap** |

三条关键原文事实：
1. **明确劝退 p 值**："we emphasize using statistical thinking but **avoid statistical significance tests** (e.g., p-value < 0.05) because of their dichotomous nature"。
2. **小 runs 数的诚实警告**："with 3 runs, bootstrap CIs underestimate the true 95% CIs"。
3. **API**：`rly.get_interval_estimates(..., reps=50000)`、`rly.create_performance_profile(...)`、
   `plot_utils.plot_performance_profiles(...)`。

> ⚠️ **本赛道的关键限定**：IQM/performance profile 是为**多任务基准（M 任务 × N run）**设计的。
> 竞赛通常是"**单一场景 + 多种子**"，此时正确做法是
> **mean/median + bootstrap 95% CI（或 IQR）**，并写清 CI 构造方式与种子数。
> **"单任务如何套用 IQM"未获证据**——不要硬套。

**可操作的统计流程模板**（来自仿真类论文的完整先例）：
`Shapiro-Wilk 正态性 → Levene 方差齐性 → 独立样本 t 检验或 Mann-Whitney U → Cohen's d 效应量 + bootstrap 95% CI`，
显著性水平 α=0.05。
依据：[MARL vs. Fixed-Time Control for Traffic Signal Optimization](https://ar5iv.labs.arxiv.org/html/2505.14544v2)

### 3.6 消融矩阵（`ablation_matrix()`）

顶会消融的三条做法：
1. **一个消融轴 = 一张图/一节**，节末给一条可执行建议
   （MAPPO：每节以加粗的 `Suggestion N: …` 收束）。
2. **目标必须写成"isolate the source of gains"**（Sable 原文），即把增益归因到组件，
   而不是"去掉它更差"。
3. **同一消融给多种聚合口径**（mean / max / final / IQM），因为口径会改变结论
   （Sable 附录 B.2 全列出）。

**消融轴清单**（顶会真实出现过的）：模块有无、输入表示、关键超参、架构替换、
关键权重敏感性、规模扫描（agent 数）。

**小规模可解释实验替代大规模消融**：QMIX 用 two-step game 的可枚举 payoff 矩阵
给出机制性证据。当大规模环境下组件差异难分辨时，这是顶会非常认可的写法。

---

## 4. 摘要（summary paragraph 的顶会变体）

### 4.1 硬性约束（官方原文）

- **ICML 2025**："Abstracts should be a single paragraph and **ideally 4-6 sentences**."
- **NeurIPS 2025 CFP**：摘要不得是占位符，明确禁止无信息量摘要
  （官方举例："We provide a new semi-supervised learning method."）。

### 4.2 七句功能骨架（本工作 `conference-narrative.md` 的顶会版）

| # | 功能 | 句式线索 | 缺失后果 |
|---|---|---|---|
| 1 | 对象现状/背景 | "<问题类> 广泛存在于 …" | — |
| 2 | **缺口句（硬）** | `However, <对象> remains unclear / under-explored.` | 动机不清，门禁报错 |
| 3 | 本文做法 | "In this work, we …" / "本文把 X 重述为 Y" | — |
| 4 | 方法要点 + **规模数字** | "on N benchmarks / 4 environments / 400 agents" | 显得没做实验 |
| 5 | **结果句（硬，带数字）** | "Our results show that … (34/45 tasks, 6.5×)" | 门禁报错 |
| 6 | 含义（可带 hedge） | "suggest … hold substantial promise" | — |
| 7 | 边界 / 代码链接 | 可选，但缺边界会与 Limitations 脱节 | — |

### 4.3 与 Nature summary paragraph 的差异（别混用）

| 维度 | Nature summary paragraph | NeurIPS/ICML/AAMAS |
|---|---|---|
| 篇幅 | ~190–300 词，7 个功能段 | ICML 硬建议 **4–6 句**单段 |
| 跨学科可读性 | **硬要求**（前 1–2 句外行可读） | 不作要求，直接进术语 |
| 主结果句 | 固定 `Here we show`，位置在中部 | 无固定语式，位置偏后 |
| 含义/展望 | 必须有更广语境段 | 常压缩为一句 hedge 或换代码链接 |
| 边界 | 结尾 bounded significance | 主要落在 Limitations / checklist |

> **本赛道建议**：正文按 ICML/NeurIPS 的 4–6 句紧凑写法（中文可到 8 句），
> 但**借鉴 Nature 的"缺口句 + 边界句"纪律**。不要照搬 Nature 的长跨学科开头。

---

## 5. 相关工作：给 gap，而不是罗列

### 5.1 两种形态都合法，最优是**并存**

- **散文**：按方法族分组（3–4 个加粗小标题），每组末句给缺口。
- **表格**：属性对比表。AAMAS 2025 的列结构可直接套：
  `Algorithm | Evaluated in | On/Off-Policy | RL Optimization | Network Architectures | Intrinsic Exploration`；
  另有一张任务表 `Benchmark | Interesting Challenges | Insights for Real-world Applications`。
- **位置**：实读的 8 篇里 Related Work 几乎都在 Section 2（方法之前）。

> **降调提醒**：Melting Pot 2.0 主动在图注里写
> "Properties highlighted here are only intended as a rough guide …
> should not be taken as a serious theoretical attempt to classify"。
> 不降调的分类表会被认为武断。

### 5.2 gap 句式模板（12 条逐字证据里提炼出的三类）

1. `However, <对象> remains unclear / unknown / under-explored.`
2. `However, <既有方法> assumes / cannot <能力> / ignores <信息>, which <后果>.`
3. `In contrast to <最接近的工作>, our method <差异点 A>, <差异点 B>.`
4. **最强的一种**：把 gap 写成"**评估体系缺陷清单**"（bullet 三条），再逐条给对策
   （AAMAS 2025 的原话："MARL evaluation does not often report the training times …
   so the results cannot be interpreted as a function of the compute budget used."）

---

## 6. 实验章节的组织与合规件

### 6.1 组织方式

- **顶会派**：拆成独立小节 —— `Evaluation protocol / Environments / Baselines / Hyperparameters / Results / Ablations`，
  超参下沉到附录（Sable、MAPPO、MATS-LP、HaSD、Melting Pot 2.0 均如此）。
- **仿真期刊派**：并入 Methodology 子节（交通信号控制论文把 `IV-A Simulation Environment`
  再拆 8 个子小节）。
- **JASSS/ODD 派**：按 ODD 七要素编号描述（`Purpose and patterns / Entities, state variables and scales /
  Process overview and scheduling / Design concepts / Initialization / Input data / Submodels`），
  正文放 **summary ODD**、完整版放补充材料、并给 **visual ODD** 图。

### 6.2 baseline 四类族谱（本工作 `csf_readiness` 会检查）

1. **规则/启发式**（fixed-time、scripted、最近出口、SPT…）
2. **单智能体 RL**（DQN/PPO 单智能体版）
3. **MARL 值分解派**（VDN / QMIX / QPLEX / QTRAN）
4. **MARL actor-critic 派**（MADDPG / MAPPO / IPPO / COMA / HAPPO）

并**必须说明各 baseline 的调参预算与本文是否对齐**（MAPPO §4.1 明确保证 grid-search 规模等价）。

### 6.3 假设前置为独立小节（强烈推荐）

AAMAS 2025 的 `§1.2 Assumptions of interest` 用 (a)–(e) 逐条列出全部前提
（CTDE、全合作、稀疏奖励、图像观测、无显式通信）。**这比放在 limitation 里强得多**：
它把局限变成"评估范围的声明"，预先挡掉"你的设置不真实"的攻击。

### 6.4 合规件（按目标会场）

| 会场 | 强制件 |
|---|---|
| NeurIPS | **paper checklist**（原文："papers not including the checklist will be desk rejected."） |
| ICML | **impact statement**（camera-ready，位于参考文献之前、不计页数） |
| 本赛事 | 按《论文规范》+ 支撑材料（完整可运行源码 + 运行环境说明） |

---

## 7. 反模式清单（20 条，均有依据）

1. 图注只写"Overview of our approach"，图里却有 4 面板 6 箭头。
2. 颜色/线型不声明语义。
3. 报 mean 却省略离散度，或不说清是 std 还是 SEM。
4. 把 bold 当"最大的那个数"，不写判据。
5. 用 p<0.05 二分法作唯一结论依据。
6. 3 个 seed 就宣称 SOTA，且不声明小样本下 CI 会低估覆盖率。
7. 把不同评估协议的分数直接同列比较。
8. 把用了预训练/额外预算的方法混进同一排名。
9. baseline 调参预算少于自己的方法。
10. 摘要只有"我们提出 X，效果很好"，无缺口句、无数字。
11. 把 Nature 的跨学科长开头搬进 ML 会场摘要。
12. 相关工作只按时间罗列，不给 gap；分类表过度声称。
13. 消融只给"去掉更差"，不给建议、不给机制。
14. 只报一种聚合口径就下结论。
15. 不写假设与失效条件（NeurIPS 明确承诺"不因诚实披露局限而扣分"，不写=放弃保护）。
16. ABM/仿真论文不给 ODD 或等价的可复现描述。
17. 仿真论文不报随机性来源与重复次数。
18. 不报 compute/训练时长，结果无法按预算解读。
19. 实验图全用位图、像素化折线。
20. 不提交 checklist / impact statement。

---

## 8. 覆盖度与"未获证据"（诚实边界）

**已获证据**：hero figure 8 例（含颜色/线型/公式/图注结构）、多面板图 7 例、
主表 4 例 + mean±std 四种写法 + seeds 实数、rliable/IQM/performance profile 原始出处与 API、
消融 3 类做法、ICML 摘要硬约束与 7 句功能拆解、Nature 六层对照、
related work 表 2 张 + gap 句式 12 条逐字、实验章节组织 6 篇实例、
完整统计流程 1 例、NeurIPS checklist #1/#2/#7/#8 与 ICML impact statement 官方原文。

**未获证据（不做推测）**：
- AAMAS 官方投稿格式与页数限制原文（官网 403）；WSC 写作规范原文（抓取失败）；
  ACM SIGSIM / AAAS / IEEE SMC 的写作范式。
- 期刊 *Simulation Modelling Practice and Theory*、*Transportation Research Part C*、
  *Physica A*、*Safety Science*、*IEEE T-ITS*、*Swarm Intelligence*、*JAAMAS*
  的**正文级**证据（本环境无法解析其 PDF）。
- "实线/虚线"的**普遍**约定（仅 CROSS 一例显式声明，故本工作标为惯例而非规范）。
- 面板标签的图内位置与字号层级规范。
- 顶会 limitation 段落的逐字范文（用 NeurIPS checklist 官方要求替代）。
- **单任务场景如何正确套用 IQM**（rliable 面向多任务；本工作给出的建议属工程判断）。

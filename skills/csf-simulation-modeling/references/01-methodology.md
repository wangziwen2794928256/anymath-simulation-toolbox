# 方法论：建模范式与算法库（A 赛道核心）

> 完整方法总库与选型决策矩阵见 `references/07-methods-library.md`；本文件是范式/校验/快速选型，07 是“问题特征→方法”的完整对照与反模式。

本文件回答三件事：**用什么范式建模、怎么校验、用什么算法求解**。引用处给出顶刊/顶会出处，赛后写论文可直接作为相关工作。

## 1. 建模范式选型（先选范式，再选算法）

| 范式 | 适合场景 | 工具/语言 | 何时用 |
|---|---|---|---|
| 基于智能体 (ABM) | 个体异质、有交互/学习/博弈、涌现行为 | Python 手写 / mesa / AnyMath 脚本 | 人群疏散、供应链多主体、群体协同 |
| 离散事件 (DES) | 排队、资源竞争、工序流转、事件驱动 | simpy / 手写事件表 | 车间调度、物流集群、RGV/AGV 调度 |
| 系统动力学 (SD) | 存量-流量、反馈回路、宏观政策 | 存量流量方程 / AnyMath 物理建模 | 宏观演化、政策评估、牛鞭效应 |
| 混合 (ABM+DES+SD) | 多层异质系统（个体+流程+宏观） | AnyMath/AnyLogic 多方法 | A 赛道大多数真题的最终形态 |

**选型口诀**：个体可辨识且有行为差异 → ABM；问题可写成事件/队列/资源 → DES；只关心总量和反馈 → SD；三者交织 → 混合，但**论文里必须讲清每层用什么、为什么**。

## 2. 模型描述与校验（决定论文可信度，A 赛道高分关键）

### 2.1 ODD 协议（Grimm et al., 2006/2010/2020, Ecol. Model. / JASSS）
描述 ABM 的标准七要素：`Overview`（目的/实体/状态/尺度）→ `Design concepts`（基本设计原理、涌现、适应、预测、感知、交互、随机性、聚集、观测）→ `Details`（初始化、输入、子模型）。竞赛论文按此写“模型建立”章节，逻辑不会乱；赛后投稿也认这套规范。

### 2.2 VV&A：校验 / 验证 / 认可（Sargent; Balci 1998 WSC）
- **Verification（代码对不对）**：单步断点、手算对拍、守恒量检查、极限/退化情形。
- **Validation（模型对不对）**：与真实数据/解析解/文献/专家常识对照；face validity；cross-validation。
- **Calibration（参数准不准）**：
  - 手调 + 敏感性分析（起步）
  - 贝叶斯优化 + 高斯过程代理模型（Kennedy & O'Hagan 2001；WSC 2024 "Calibrating Digital Twins via Bayesian Optimization with Root Finding"）
  - History Matching（高维、昂贵仿真）
  - 仿真-优化闭环：数据 → 参数标定 → 仿真 → 误差 → 迭代（C 赛道通用）

**竞赛最小闭环**：每个子问题结尾都要有“模型检验”段落（0.5–1 页），否则评委会扣分。

## 3. 算法库（按 A 赛道可能命题分类）

### 3.1 调度 / 车间 / 物流集群（对应 2025 A 题“智能流水车间调度”）
- **分派规则（基线，必做）**：SPT / LPT / EDD / Slack / CR / MWKR / 组合规则。先跑这些当 baseline。
- **元启发式**：遗传算法 GA（Reeves 1995）、**NSGA-II**（Deb et al., IEEE TEC 2002）多目标、NSGA-III（Deb & Jain, IEEE TEC 2014）高维目标、模拟退火、禁忌搜索、粒子群。
- **精确/混合**：CP（约束规划，IBM CP Optimizer）、Gurobi/CPLEX 数学规划——用于小规模验证上界。
- **DRL 调度**：DQN/PPO + 析取图/图神经网络；综述见 Knowledge-Based Systems 2025 "Deep RL for job shop scheduling: a comprehensive review"。
- **目标函数转化（评分最爱）**：把“效率最高”写成“8 小时产能最大/设备空闲时间最小/加权延期最小”，并给出与理想状态的效率比。

### 3.2 人群疏散 / 行为演化（对应“社会人群行为演化”）
- **元胞自动机 CA**（Burstedde et al., Physica A 2001；Kirchner & Schadschneider 2002）：简单、可视化好，适合当 baseline。
- **社会力模型**（Helbing & Molnár, PRE 1995）：连续空间人群动力学，经典、可发论文。
- **ABM + A*/势场**：个体寻路 + 拥塞惩罚；加情绪/出口选择/领导-跟随机制。
- **MARL 疏散**：QMIX/MAPPO 分布式决策 + 实时拥塞/危险惩罚（ISPRS Archives 2026 "Congestion-aware MARL for wildfire evacuation routing"；AAMAS 2026 LLM-guided evacuation）。
- **评价指标**：总疏散时间、单位时间流出量、瓶颈利用率、不同出口/策略对比。

### 3.3 供应链 / 多主体协同 / 博弈
- 系统动力学建模“牛鞭效应”（Forrester 啤酒游戏 / Sterman 1989, Manage. Sci.）。
- 多智能体供应链：供应商-制造商-分销商-零售商 Agent + 补货策略对比。
- 演化博弈（ESS / 复制者方程）用于多主体策略演化。
- 协同与通信：图神经网络 + MARL（QMIX/MAPPO/CommNet）。

### 3.4 MARL 算法谱系（你们的主打差异化武器）
| 算法 | 类型 | 适用 | 出处 |
|---|---|---|---|
| IQL | 独立学习 | 简单基线 | Tan 1993 |
| VDN | 值分解 | 合作，可加价值 | Sunehag et al., AAMAS 2018 |
| QMIX | 值分解（单调混合） | 合作，部分可观测 | Rashid et al., ICML 2018 |
| QPLEX/QTRAN | 值分解改进 | 更复杂信用分配 | Wang et al., ICML 2021 / Son et al., ICML 2019 |
| MADDPG | CTDE，连续动作 | 混合动机 | Lowe et al., NeurIPS 2017 |
| MAPPO | CTDE，on-policy | 合作，样本利用率高 | Yu et al., NeurIPS 2022 D&B |

**选型原则**：能写成“合作任务 + 全局奖励”先用 **QMIX/MAPPO**；离散动作用值分解，连续动作用 MADDPG；不确定时 **PPO 家族（MAPPO/IPPO）最稳**。永远保留 IQL/规则作为 baseline。

### 3.5 优化实验框架（AnyMath 自带，也可本地等价实现）
- 参数变化实验、蒙特卡洛、敏感性分析、优化实验、校准/比较实验、强化学习实验。
- 本地等价：`optuna`（贝叶斯/TPE 超参）、`deap`（GA）、`scikit-optimize`、`stable-baselines3`。

## 4. 数字孪生 / 数据驱动（备选 C 赛道 / 论文加分项）
- 五维数字孪生模型（Tao et al.）：物理实体 + 虚拟模型 + 服务 + 数据 + 连接。
- 数据驱动仿真优化闭环（WSC 2024 tutorial "Data-Driven Simulation Optimization in the Age of Digital Twins"）。
- 代理模型：高斯过程（GP）、神经网络代理 + 贝叶斯优化，解决“仿真太贵”的问题。

## 5. 赛后论文的“方法论站位”
- 竞赛作品升维成论文的常见公式：**问题场景 × 建模范式（ABM/DES/SD）× 学习/优化算法（MARL/NSGA-II/DRL）× 真实数据校准**。
- 新颖性至少来自其一：① 新场景；② 新机制（如把情绪/通信/拥塞引入 Agent）；③ 新算法组合；④ 新校准流程。

---

## 6. 现代方法（2024–2026 前沿，竞赛加分 + 赛后发论文利器）

### 6.1 LLM / 生成式智能体仿真（A 赛道“行为演化/协同”的新武器）
- 范式演进：从“规则 Agent”到“语言接地 Agent”（Generative ABM / GABM）。
- 里程碑：Generative Agents（Park et al., UIST 2023，Smallville 小镇实验）；LLM-based Multi-Agents 综述（Guo et al. 2024）；LLM 社会仿真综述（Gao et al. 2024）；"Do LLMs Solve the Problems of ABM?"（arXiv:2504.03274）。
- 适合做的点：给智能体加**记忆、反思、规划、沟通**，观察涌现行为；用 LLM 做策略生成/偏好建模，再用规则/RL 兜底保证可复现。
- 注意：LLM 不可复现、贵、慢，**竞赛 4 天里只能当“加分机制”或论文讨论，不能当主模型**；主模型仍是可复现的规则/RL。

### 6.2 MARL 框架与基准（工程落地，别手写轮子）
- **EPyMARL**（Papoudakis et al., JMLR 2021）：QMIX/MAPPO/IQL 等现成实现，MPE 基准。
- **PyMARLzoo+**（AAMAS 2025 扩展）：PettingZoo/Overcooked/Pressure Plate 等 8 个合作基准 + 7 个 SOTA 算法（HAPPO 等）。
- **PettingZoo**（Terry et al., NeurIPS 2021）：多智能体 Gym 接口；**MPE**（多粒子环境）当轻量实验台。
- 决策：离散合作 → QMIX/MAPPO（EPyMARL）；连续/混合 → MADDPG/MAPPO；要快 → SB3 的 PPO 单策略共享（IPPO）。

### 6.3 GNN / Transformer 调度（2025–2026 调度题主流）
- 表示：析取图（disjunctive graph）→ 异构图 GNN（工序-机器-工件节点 + 边类型）。
- 组合：GNN 编码 + DRL 决策（GAT-DDQN、PG-DDQN、MP-GRL、Dual Operation Aggregation GNN，WWW 2025）。
- 综述：Chen et al. "Graph Neural Networks for JSP: A Survey"（arXiv:2406.14096）；"Machine learning for scheduling: from designing solvers to learning-enabled decision systems"（arXiv:2512.22642）。
- 竞赛落地：小规模用析取图 + GAT + PPO；没时间就 GA/NSGA-II + 分派规则，论文里提 GNN 作为改进方向。

### 6.4 数字孪生 + 数据驱动仿真优化
- 五维数字孪生（Tao et al.）；Data-Driven Simulation Optimization（WSC 2024）；贝叶斯优化校准（BO + GP 代理）。
- 实用闭环：`真实数据 → 参数标定(BO) → 仿真 → 误差 → 迭代`，评审眼里的“高级感”来源。

## 7. 模型选型决策（按命题类型快速定位）

```
先问：题目给的是“个体/群体”还是“流程/资源”还是“总量/反馈”？
├─ 个体可辨识、有行为差异 → ABM（+ 可选 LLM 行为机制）
├─ 可写成事件/队列/资源竞争 → 离散事件 DES（simpy）
├─ 只关心总量与反馈回路 → 系统动力学 SD
└─ 三者交织 → 混合范式，论文写清“分层 + 交互”

再问：要“推演”还是“优化/决策”？
├─ 只要推演/预测 → 校准好参数的仿真模型即可
├─ 要优化/调度 → 规则基线 + 元启发式(NSGA-II/GA/PSO) 或 DRL(PPO/GNN)
└─ 要多主体协作决策 → MARL（离散合作 QMIX/MAPPO，连续 MADDPG/MAPPO）

最后问：数据足不足？
├─ 数据充分 → 数据驱动校准 + 学习型策略（C 思路）
├─ 数据稀缺 → 机理 + 规则 + 敏感性分析，用少量数据标定关键参数
└─ 完全无数据 → 机理 + 假设 + 极限/解析解验证
```

**选择铁律**：先求“可解释、可复现、能跑通”，再求“新颖、复杂”；任何 ML/RL 都要配规则 baseline 对照，否则评委不买账。

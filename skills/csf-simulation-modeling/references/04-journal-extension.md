# 赛后扩展：竞赛作品 → Q2–Q4 SCI / 会议论文

竞赛结束不等于结束：把作品打磨成论文。**能否发表，取决于你从第一天起留了多少“论文级资产”**（baseline、种子、超参、源码、指标、消融）。

## 1. 先定位“论文的新颖性”（四选一即可）
1. 新场景：把赛题场景换成更完整/真实的开放数据场景。
2. 新机制：给 Agent 加情绪、通信、拥塞、领导-跟随、异构策略等。
3. 新算法：MARL 值分解/CTDE 改进、DRL 调度、NSGA-III、混合启发式。
4. 新校准流程：贝叶斯优化/代理模型校准仿真参数。

**通用公式**：`问题场景 × 建模范式(ABM/DES/SD) × 学习/优化算法(MARL/DRL/NSGA-II) × 真实数据校准`。

## 2. 论文骨架（IMRaD）
- Title / Abstract / Keywords
- 1. Introduction（motivation + contributions 分点列出 + 组织结构）
- 2. Related Work（建模范式、算法、场景三方综述，引用顶刊顶会）
- 3. Problem Formulation（符号、目标、约束）
- 4. Method（框架图 + 模型/算法细节，可复现到公式级）
- 5. Experiments（数据集、指标、基线、消融、敏感性、可复现声明）
- 6. Conclusion（贡献、局限、未来工作）

## 3. 投稿目标（按难度/匹配度分层）

### 方法级（难度高，冲 Q1–Q2）
- **JASSS**（Journal of Artificial Societies and Social Simulation，Q1）：ABM/社会仿真领域的顶级匹配刊，接受 ODD 描述与复现研究。
- **Expert Systems with Applications**（Q1）、**Computers & Industrial Engineering**（Q1）：调度/优化/智能系统。
- **Applied Soft Computing**（Q1/Q2）、**Knowledge-Based Systems**（Q1）：DRL 调度、软计算。
- 会议：**AAMAS**（多智能体）、**WSC**（Winter Simulation Conference，仿真旗舰）、**ICCPS/CASE**。

### 应用/仿真级（Q2–Q3，最匹配本赛事“仿真建模”）
- **Simulation Modelling Practice and Theory**（Elsevier，Q2/Q3，SMPT）：系统仿真与建模的理论、方法、应用、验证、算法——**赛后首选投稿目标**。
- **Journal of Simulation**（Taylor & Francis）、**International Journal of Simulation and Process Modelling**。
- **IEEE Access**（Q2，快，但注意近年声誉，作为保底）。
- **ACM Transactions on Modeling and Computer Simulation (TOMACS)**。

### 快速出版/Q4 保底（MDPI 等，周期短）
- Applied Sciences、Mathematics、Systems、Sustainability、Processes、Electronics、Entropy。
- 注意：MDPI 对“应用型 + 充足实验”友好，但审稿人对新颖性要求逐年提高；保证实验和复现完整。

### 交通/物流特化（若赛题是交通疏散/物流）
- IEEE Transactions on Intelligent Transportation Systems、Transportation Research Part C（Q1，难度高）；Sustainability/Applied Sciences 的交通专刊（Q2–Q4 保底）。

## 4. 从“竞赛版”到“投稿版”的 6 个动作
1. 补 related work（用 01-methodology.md 里标注的顶刊顶会出处）。
2. 把“规则 baseline”升级为至少 3 个公开 SOTA 基线（如 IQL/QMIX/MAPPO 或 NSGA-II/GA/PSO）。
3. 做消融实验（ablation）：去掉某机制，指标掉多少，证明贡献。
4. 多 seed + 显著性（mean±std，必要时 Wilcoxon/t-test）。
5. 可复现声明：开源代码 + 参数 + 种子 + 运行命令。
6. 英文重写：先中文逻辑打底，再用规范英文学术表达；图和表全部英文化。

## 5. 风险提示
- 不要拿竞赛论文原样投（查重/自抄袭/AIGC 风险，且结构不符）。
- 选刊先看 scope 匹配，再谈分区；SMPT/JASSS 对“仿真”的认可度高于纯 ML 刊。
- 预留 2–4 个月审稿周期；MDPI 快刊 1–3 个月；顶会（AAMAS/WSC）有明确截稿，提前规划。

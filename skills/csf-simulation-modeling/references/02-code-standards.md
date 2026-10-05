# 代码可读性 / 质量 / 复现规范

目标：让评委（查支撑材料时）和未来的自己（赛后发论文时）都能 10 分钟看懂、一键复现。

## 1. 目录约定（与工作站一致）
```
01-模型与算法/src/   # 可复用模块：config / common / env / agent / algorithm
01-模型与算法/notebooks/  # EDA 与原型（不进入最终整洁代码）
02-实验与结果/scripts/    # 实验入口（参数扫描/蒙特卡洛/敏感性）
02-实验与结果/outputs/<run_id>/  # 产物，不入库
03-论文与支撑材料/  04-演示视频/
```

## 2. 核心规范（强制）
- **配置集中**：所有参数进 `config.py`（dataclass 或 dict），禁止散落魔法数字；每个参数写清含义与来源（题给/标定/假设）。
- **固定种子**：`common.seed_everything(seed)` 必须覆盖 random/numpy/torch；实验跑多个 seed。
- **可复现输出**：结果统一存 `outputs/<run_id>/`，`run_id` 带策略名+种子；同时落 `config.json`，保证“图↔参数↔代码”可对应。
- **类型标注**：用 dataclass 定义 Agent/Config，函数带 type hints，返回结构清晰（`step -> (obs, reward, done, info)`）。
- **单一职责**：`env`（动力学）与 `agent/policy`（决策）分离；`experiment` 只管跑，不管建模。
- **日志**：关键步骤、指标、耗时写日志；不要只靠 print。
- **docstring**：每个模块/类说明“输入-输出-副作用”，Agent 状态变量逐条注释。
- **可运行检查**：附录源程序必须能跑；跑不通或与论文不符可能取消资格。若没用程序要写明。

## 3. 代码质量工具（本地 Mac 直接可用）
- `ruff`：lint + format（替代 flake8/black，快）。
- `pytest`：给“规则/目标函数/事件推进”写最小单测（这是评审眼里专业的信号）。
- 推荐 `pyproject.toml` 配置见 `assets/code-template/pyproject.toml`。

## 4. 实验设计（决定论文上不上得了台面）
- 每次实验三要素齐全：**假设 → 实验 → 指标**，用表格记录，别只跑一个数。
- 必做四类：① 基线 vs 创新；② 敏感性分析（关键参数 ±10%/±20%）；③ 蒙特卡洛（多次 seed 报 mean±std）；④ 与解析解/已知极限/文献对照。
- 多机并行：不同机器用不同 `--run-id` 前缀，最后合并；统一种子协议。

## 5. 回传 AnyMath（Win）兼容清单
- 统一 `pathlib.Path`，不手拼路径；不写死 `/Users/...`。
- 中文字体 matplotlib 在 Win 用 `SimHei`/`Microsoft YaHei`。
- Python 代码以 `ipynb` 导出到 AnyMath；Julia 用 `jl`；物理连续系统用 EngeeModel。
- 三块 NVIDIA 卡装 CUDA 版 PyTorch 跑 `stable-baselines3`。

## 6. 写给“论文级”代码的最小门槛
- 别人能一键 `pip install -r requirements.txt && python scripts/run_experiments.py --mode mc` 复现你的主结果。
- 提交前跑一遍 `ruff check`、`pytest`，清空 notebook 输出与临时文件。

---

## 7. 算法实现能力（本赛道常用指标 + 代码模式）

### 7.1 评价指标库（论文和代码都要统一口径）
- 调度/车间：makespan（最大完工时间）、平均流经时间、设备利用率、加权延期（tardiness）、准时交付率。
- 疏散/人群：总疏散时间、单位时间流出量、瓶颈利用率、平均/最大拥堵密度。
- 供应链/物流：库存水平、牛鞭效应幅值、服务水平（fill rate）、总成本。
- RL 训练：episode return、成功率、收敛步数；报告 mean±std（≥3 seeds）。

### 7.2 算法分层（从简到繁，逐级替换，永远留基线）
1. **规则基线**：贪心/最短处理时间/最早交期/随机 → `RulePolicy`。
2. **元启发式**：GA / NSGA-II / PSO / 模拟退火 → 用 `deap` 或自写，输出帕累托前沿。
3. **单智能体 DRL**：DQN/PPO（SB3）→ `gym_env.py` 包装。
4. **多智能体 MARL**：IPPO（SB3 PPO 参数共享，最稳）→ 进阶 QMIX/MAPPO 用 EPyMARL/PyMARLzoo+。
5. **GNN/Transformer**：析取图 + GAT/注意力编码（竞赛时间不够则只在论文里作为改进方向）。

### 7.3 训练工程要点（评委/审稿人都认）
- 多 seed（≥3）报告 mean±std；EvalCallback 存最优模型（见 `assets/code-template/train_marl.py`）。
- 奖励与 KPI 单调对齐且尽量稠密；归一化状态；固定 episode 长度或加早停。
- 保存：config.json + summary.json + 最优模型；图↔参数↔结果可追溯。
- 消融：去掉关键机制跑一遍，证明贡献（赛后论文必做）。

### 7.4 自检命令
```bash
ruff check . && pytest          # 静态检查 + 单测
python scripts/run_experiments.py --mode mc --run-id smoke --repeats 5
python assets/code-template/train_marl.py --run-id ippo_smoke --seeds 2 --total-timesteps 20000
```

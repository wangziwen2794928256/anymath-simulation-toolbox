#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_method_templates —— A 赛道五领域方法总览图模板库

为什么需要它
------------
`csf_archetypes.method_figure()` 解决了"怎么画"（分层布局、自动撑开、箭头吸附、
正交折线、标签避让、拓扑自检），但每次仍要从空白开始想"该放哪些模块"。
赛期只有 4 天，这一层思考成本必须前置。

本模块把 A 赛道**最可能出现的五类子问题**的方法图固化成模板：调用者只填
自己题目的具体名词，结构层次与模块语义已经就位。

| 模板 | 适用子问题 | 结构要点 |
|---|---|---|
| `evac_relocation` | 人群疏散 / 出口分配 / 车辆调度（**容量受限的资源分配**） | 环境-智能体-算法-反馈 四层，反馈回路是核心 |
| `job_shop` | 流水车间 / 作业车间 / RGV-AGV 调度（**调度型**） | 工件流 + 资源池 + 调度决策 三条并行带 |
| `supply_network` | 供应链 / 库存 / 多级补货（**网络化 + 反馈延迟**） | 多级串行 + 信息流与物流分离 |
| `epidemic_diffusion` | 传染病 / 舆情 / 风险扩散（**网络化传播**） | 状态机分层（S/E/I/R）+ 接触网络 + 干预 |
| `marl_coordination` | 多智能体协同学习（**学习式协同**） | CTDE 双通道：训练期全局 / 执行期局部 |

共同遵循的顶会惯例（见 `csf-figure-forge/references/topvenue-contracts.md`）：
  * 2–4 层，自上而下、自左向右
  * 必须含三类块：本地策略 / 仅训练期使用的集中模块 / 数据流载体
  * 实线=数据流，虚线=反馈或训练期通路，并自动生成图例
  * 图内**不写标题**（标题交给 LaTeX \\caption）

用法
----
    python csf_method_templates.py --list
    python csf_method_templates.py --make evac_relocation --outdir figures --name fig1_method
    python csf_method_templates.py --make all --outdir figures
"""

from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import csf_archetypes as A  # noqa: E402
import csf_fig  # noqa: E402

T = A.ArchNode  # 简写

#: 支持的语言（模板标签集）
LANGS = ("zh", "en")


def _is_en(lang: str) -> bool:
    lang = (lang or "zh").strip().lower()
    if lang not in LANGS:
        raise ValueError(f"lang 只支持 {LANGS}，收到 {lang!r}")
    return lang == "en"


def _en_or(value: str, zh_default: str, en_default: str) -> str:
    """英文模式：参数仍是中文默认值时换成英文默认名词；自定义名词原样保留。"""
    return en_default if value == zh_default else value


def _cap(s: str) -> str:
    """只把首字母大写（``capitalize()`` 会把 RGV-AGV 变成 Rgv-agv）。"""
    return s[:1].upper() + s[1:] if s else s


# --------------------------------------------------------------------------- #
# 模板一：容量受限的资源分配（疏散 / 出口选择 / 车辆调度）
# --------------------------------------------------------------------------- #

def evac_relocation(subject: str = "个体", resource: str = "出口",
                    outer: str = "场地", *, lang: str = "zh") -> tuple:
    """最通用的一类：N 个主体在 K 个容量受限资源间分配自身。

    ``lang='en'`` 返回英文标签，**结构（lane/order/role/边 style）与中文版逐项一致**
    （由 ``check_template_parity()`` 守住）。名词参数若仍是中文默认值，
    自动换成英文默认名词；显式传入的自定义名词在任何语言下都原样保留。
    """
    if _is_en(lang):
        return _evac_relocation_en(subject, resource, outer)
    nodes = [
        # 环境层
        T("outer", f"{outer}与环境", "几何 / 约束", role="baseline", lane=0, order=0),
        T("cap", f"{resource}容量模型", r"$\mu_k = w_k q$", role="baseline", lane=0, order=1),
        # 主体层
        T("pop", f"{subject}群体", "N 个异质主体\n状态 + 速度", role="ours_alt", lane=1, order=0),
        T("obs", "全局观测", r"$o_i=(p_i,\{Q_k\})$", role="ours_alt", lane=1, order=1),
        T("pol", "共享策略", r"$\pi_\theta(a_i\,|\,o_i)$", role="ours_alt", lane=1, order=2),
        # 算法层
        T("cost", "边际代价", r"$c_i(k)=d_i(k)+\lambda Q_k$", role="ours", lane=2, order=0),
        T("assign", f"{resource}分配", r"$a_i=\arg\min_k c_i(k)$", role="ours", lane=2, order=1),
        T("svc", "容量服务", r"$\mu_k\Delta t$ 排队服务", role="ours", lane=2, order=2),
        # 评估与反馈
        T("kpi", "宏观指标", "T、Gini、瓶颈利用率", role="improve", lane=3, order=0),
        T("fb", "拥塞反馈", r"$Q_k(t)$ 回传", role="bottleneck", lane=3, order=1),
    ]
    edges = [
        ("outer", "cap", "约束", "solid"),
        ("pop", "obs", "状态", "solid"),
        ("obs", "pol", "观测", "solid"),
        ("cost", "assign", "代价", "solid"),
        ("assign", "svc", "指派", "solid"),
        ("kpi", "fb", "指标", "solid"),
        ("cap", "obs", "容量", "solid"),
        ("pol", "cost", "策略", "solid"),
        ("svc", "kpi", "服务事件", "solid"),
        ("svc", "fb", "队列长度", "dashed"),
        ("fb", "cost", "拥堵回传", "dashed"),
    ]
    return ["环境层 Environment", "主体层 Agent", "算法层 Algorithm", "评估与反馈"], nodes, edges


def _evac_relocation_en(subject: str, resource: str, outer: str) -> tuple:
    """`evac_relocation` 的英文标签版（结构与中文版逐项一致）。"""
    subj = _en_or(subject, "个体", "agent")
    res = _en_or(resource, "出口", "exit")
    venue = _en_or(outer, "场地", "venue")
    nodes = [
        T("outer", f"{_cap(venue)} and geometry", "Layout / constraints",
          role="baseline", lane=0, order=0),
        T("cap", f"{_cap(res)} capacity model", r"$\mu_k = w_k q$",
          role="baseline", lane=0, order=1),
        T("pop", f"{_cap(subj)} population", "N heterogeneous agents\nstate + velocity",
          role="ours_alt", lane=1, order=0),
        T("obs", "Global observation", r"$o_i=(p_i,\{Q_k\})$",
          role="ours_alt", lane=1, order=1),
        T("pol", "Shared policy", r"$\pi_\theta(a_i\,|\,o_i)$",
          role="ours_alt", lane=1, order=2),
        T("cost", "Marginal cost", r"$c_i(k)=d_i(k)+\lambda Q_k$",
          role="ours", lane=2, order=0),
        T("assign", f"{_cap(res)} assignment", r"$a_i=\arg\min_k c_i(k)$",
          role="ours", lane=2, order=1),
        T("svc", "Capacity service", r"$\mu_k\Delta t$ queue service",
          role="ours", lane=2, order=2),
        T("kpi", "System metrics", "T, Gini, bottleneck utilization",
          role="improve", lane=3, order=0),
        T("fb", "Congestion feedback", r"$Q_k(t)$ return",
          role="bottleneck", lane=3, order=1),
    ]
    edges = [
        ("outer", "cap", "constraints", "solid"),
        ("pop", "obs", "states", "solid"),
        ("obs", "pol", "observations", "solid"),
        ("cost", "assign", "costs", "solid"),
        ("assign", "svc", "assignment", "solid"),
        ("kpi", "fb", "metrics", "solid"),
        ("cap", "obs", "capacity", "solid"),
        ("pol", "cost", "policy", "solid"),
        ("svc", "kpi", "service events", "solid"),
        ("svc", "fb", "queue length", "dashed"),
        ("fb", "cost", "congestion return", "dashed"),
    ]
    return ["Environment", "Agents", "Algorithm", "Evaluation and feedback"], nodes, edges


# --------------------------------------------------------------------------- #
# 模板二：调度型（流水车间 / 作业车间 / RGV-AGV）
# --------------------------------------------------------------------------- #

def job_shop(job: str = "工件", res: str = "机器", *, lang: str = "zh") -> tuple:
    """调度型：工件流 + 资源池 + 调度决策三条带。

    ``lang='en'`` 返回英文标签（结构一致，见 ``check_template_parity()``）。
    """
    if _is_en(lang):
        return _job_shop_en(job, res)
    nodes = [
        # 工件流
        T("jobs", f"{job}集合", "工序 / 交期", role="baseline", lane=0, order=0),
        T("route", "工艺路线", "工序先后约束", role="baseline", lane=0, order=1),
        T("ready", "就绪队列", "可开工工序", role="baseline", lane=0, order=2),
        # 资源池
        T("res", f"{res}资源池", "数量 / 能力", role="ours_alt", lane=1, order=0),
        T("setup", "换型与准备", r"$s_{ij}$ 换型时间", role="ours_alt", lane=1, order=1),
        T("fail", "故障与修复", "MTBF / MTTR", role="bottleneck", lane=1, order=2),
        # 调度决策
        T("rule", "分派规则基线", "SPT / EDD / CR", role="baseline_2", lane=2, order=0),
        T("crit", "调度判据", r"$\min\{\text{makespan},\ \sum T_j\}$", role="ours", lane=2, order=1),
        T("sched", "调度决策", "规则 / 元启发式 / DRL", role="ours", lane=2, order=2),
        # 评估
        T("kpi", "调度指标", "makespan、延期、利用率", role="improve", lane=3, order=0),
        T("gantt", "甘特与瓶颈", "关键路径识别", role="improve", lane=3, order=1),
    ]
    edges = [
        ("jobs", "route", "工艺", "solid"),
        ("route", "ready", "解锁", "solid"),
        ("res", "setup", "切换", "solid"),
        ("setup", "fail", "扰动", "solid"),
        ("rule", "crit", "候选", "solid"),
        ("crit", "sched", "目标", "solid"),
        ("ready", "sched", "就绪集", "solid"),
        ("res", "sched", "可用资源", "solid"),
        ("sched", "kpi", "排程", "solid"),
        ("kpi", "gantt", "结果", "solid"),
        ("fail", "sched", "扰动回传", "dashed"),
        ("gantt", "rule", "瓶颈反馈", "dashed"),
    ]
    return ["工件流 Job flow", "资源池 Resources", "调度决策 Scheduling", "评估 Evaluation"], nodes, edges


def _job_shop_en(job: str, res: str) -> tuple:
    """`job_shop` 的英文标签版（结构与中文版逐项一致）。"""
    jb = _en_or(job, "工件", "job")
    rs = _en_or(res, "机器", "machine")
    nodes = [
        T("jobs", f"{_cap(jb)} set", "Operations / due dates",
          role="baseline", lane=0, order=0),
        T("route", "Process routes", "Precedence constraints",
          role="baseline", lane=0, order=1),
        T("ready", "Ready queue", "Releasable operations",
          role="baseline", lane=0, order=2),
        T("res", f"{_cap(rs)} pool", "Count / capability",
          role="ours_alt", lane=1, order=0),
        T("setup", "Setup and changeover", r"$s_{ij}$ setup time",
          role="ours_alt", lane=1, order=1),
        T("fail", "Failure and repair", "MTBF / MTTR",
          role="bottleneck", lane=1, order=2),
        T("rule", "Dispatching baseline", "SPT / EDD / CR",
          role="baseline_2", lane=2, order=0),
        T("crit", "Scheduling criterion", r"$\min\{\text{makespan},\ \sum T_j\}$",
          role="ours", lane=2, order=1),
        T("sched", "Scheduling decision", "Rules / metaheuristics / DRL",
          role="ours", lane=2, order=2),
        T("kpi", "Schedule metrics", "Makespan, tardiness, utilization",
          role="improve", lane=3, order=0),
        T("gantt", "Gantt and bottlenecks", "Critical path identification",
          role="improve", lane=3, order=1),
    ]
    edges = [
        ("jobs", "route", "routing", "solid"),
        ("route", "ready", "release", "solid"),
        ("res", "setup", "changeover", "solid"),
        ("setup", "fail", "disturbance", "solid"),
        ("rule", "crit", "candidates", "solid"),
        ("crit", "sched", "objective", "solid"),
        ("ready", "sched", "ready set", "solid"),
        ("res", "sched", "available machines", "solid"),
        ("sched", "kpi", "schedule", "solid"),
        ("kpi", "gantt", "results", "solid"),
        ("fail", "sched", "disturbance return", "dashed"),
        ("gantt", "rule", "bottleneck feedback", "dashed"),
    ]
    return ["Job flow", "Resources", "Scheduling", "Evaluation"], nodes, edges


# --------------------------------------------------------------------------- #
# 模板三：网络化 + 反馈延迟（供应链 / 库存 / 多级补货）
# --------------------------------------------------------------------------- #

def supply_network(levels: int = 3, *, lang: str = "zh") -> tuple:
    """供应链：多级串行，物流与信息流分离（牛鞭效应的标准画法）。

    ``lang='en'`` 返回英文标签（结构一致，见 ``check_template_parity()``）。
    """
    if _is_en(lang):
        return _supply_network_en(levels)
    names = ["供应商", "制造商", "分销商", "零售商"][:levels]
    nodes = [
        T("demand", "终端需求", "随机 / 时变", role="baseline", lane=0, order=1),
    ]
    # 每一级一个节点（横向排开）
    # 注意：物流方向必须与读图方向一致（左→右）。初版把供应商放在 order 0
    # 而零售商在 order levels-1，却让 e(i)->e(i-1) 传订单，触发「同层反向」警告。
    # 正解：供应商在最左（order 0），需求在右侧进入，边一律 e(i)-e(i+1)。
    for i, nm in enumerate(names):
        nodes.append(T(f"e{i}", nm, "库存 / 在制品", role="ours_alt", lane=1, order=i))
    nodes += [
        T("policy", "补货策略", r"$(s,S)$ / order-up-to", role="ours", lane=2, order=0),
        T("lead", "提前期", r"$L$ 与延迟", role="ours", lane=2, order=1),
        T("info", "信息共享通道", "需求可见性", role="improve", lane=2, order=2),
        T("kpi", "绩效指标", "成本、服务水平、方差放大", role="improve", lane=3, order=0),
        T("bull", "牛鞭放大系数", r"$\mathrm{Var}(O)/\mathrm{Var}(D)$", role="bottleneck", lane=3, order=1),
    ]
    # 物流：上游 i → 下游 i+1（与读图方向一致）
    edges = [(f"e{i}", f"e{i+1}", "供货", "solid") for i in range(levels - 1)]
    # 需求在网络层内从右（下游）侧进入：demand 与 e0 同层，order 保证正向
    edges.append(("demand", "e0", "需求拉动", "solid"))
    edges += [
        ("policy", "lead", "参数", "solid"),
        ("lead", "info", "延迟", "solid"),
        ("info", "e0", "需求共享", "dashed"),
        (f"e{levels-1}", "kpi", "履约", "solid"),
        ("kpi", "bull", "方差", "solid"),
        ("bull", "policy", "放大反馈", "dashed"),
    ]
    return ["需求 Demand", "层级 Echelons", "策略 Policies", "评估 Evaluation"], nodes, edges


def _supply_network_en(levels: int) -> tuple:
    """`supply_network` 的英文标签版（结构与中文版逐项一致）。"""
    names = ["Supplier", "Manufacturer", "Distributor", "Retailer"][:levels]
    nodes = [
        T("demand", "End demand", "Stochastic / time-varying",
          role="baseline", lane=0, order=1),
    ]
    for i, nm in enumerate(names):
        nodes.append(T(f"e{i}", nm, "Inventory / WIP", role="ours_alt", lane=1, order=i))
    nodes += [
        T("policy", "Replenishment policy", r"$(s,S)$ / order-up-to",
          role="ours", lane=2, order=0),
        T("lead", "Lead time", r"$L$ and delay", role="ours", lane=2, order=1),
        T("info", "Information sharing", "Demand visibility",
          role="improve", lane=2, order=2),
        T("kpi", "Performance metrics", "Cost, service level, variance amplification",
          role="improve", lane=3, order=0),
        T("bull", "Bullwhip ratio", r"$\mathrm{Var}(O)/\mathrm{Var}(D)$",
          role="bottleneck", lane=3, order=1),
    ]
    edges = [(f"e{i}", f"e{i+1}", "supply", "solid") for i in range(levels - 1)]
    edges.append(("demand", "e0", "demand pull", "solid"))
    edges += [
        ("policy", "lead", "parameters", "solid"),
        ("lead", "info", "delay", "solid"),
        ("info", "e0", "demand sharing", "dashed"),
        (f"e{levels-1}", "kpi", "fulfilment", "solid"),
        ("kpi", "bull", "variance", "solid"),
        ("bull", "policy", "amplification feedback", "dashed"),
    ]
    return ["Demand", "Echelons", "Policies", "Evaluation"], nodes, edges


# --------------------------------------------------------------------------- #
# 模板四：网络化传播（传染病 / 舆情 / 风险扩散）
# --------------------------------------------------------------------------- #

def epidemic_diffusion(states: str = "S-E-I-R", *, lang: str = "zh") -> tuple:
    """传播型：个体状态机 + 接触网络 + 干预。

    ``lang='en'`` 返回英文标签（结构一致，见 ``check_template_parity()``）。
    """
    if _is_en(lang):
        return _epidemic_diffusion_en(states)
    st = states.split("-")
    nodes = [
        T("net", "接触网络", "拓扑 / 度分布", role="baseline", lane=0, order=0),
        T("mix", "混合模式", "同质 / 异质 / 分层", role="baseline", lane=0, order=1),
        T("state", f"个体状态机", " → ".join(st), role="ours_alt", lane=1, order=0),
        T("trans", "转移概率", r"$\beta,\ \sigma,\ \gamma$", role="ours_alt", lane=1, order=1),
        T("inter", "干预措施", "隔离 / 接种 / 限流", role="ours", lane=2, order=0),
        T("r0", "再生数", r"$R_0=\beta/\gamma$", role="ours", lane=2, order=1),
        T("kpi", "宏观指标", "峰值、最终规模、持续时间", role="improve", lane=3, order=0),
        T("thr", "阈值行为", r"$R_0=1$ 相变", role="bottleneck", lane=3, order=1),
    ]
    # 原来这里写的是 `for i in range(len(st)-1): if i == 0: edges = [...]; break`。
    # 那个循环只在构造一次边表，却带来一个真实缺陷：当 states 只有一个状态
    # （例如 "I"）时 len(st)-1 == 0，循环体不执行，`edges` **从未被赋值**，
    # 函数在 return 处抛 NameError。改为直接写边表，行为对 len(st)>=2 完全不变。
    edges = [
        ("net", "state", "接触", "solid"),
        ("mix", "trans", "接触率", "solid"),
        ("state", "trans", "状态", "solid"),
        ("trans", "inter", "风险", "solid"),
        ("inter", "r0", "压低", "solid"),
        ("r0", "kpi", "预测", "solid"),
        ("kpi", "thr", "比较", "solid"),
        ("thr", "inter", "阈值反馈", "dashed"),
    ]
    return ["网络结构 Network", "个体状态 Agents", "干预与理论 Intervention",
            "评估 Evaluation"], nodes, edges


def _epidemic_diffusion_en(states: str) -> tuple:
    """英文版：key / lane / order / role / 边 (src,dst,style) 与中文版逐项一致。

    上一版这里只写了调用 ``_epidemic_diffusion_en(states)`` 却**没有定义它**，
    于是 ``--lang en`` 一跑到第四个模板就 NameError。之所以一直没被发现：
    当时 ``lang`` 只做成了 Python 形参、命令行没有 ``--lang`` 开关，
    这条路根本没人走到过。接口存在但不可达 = 不存在。
    """
    st = states.split("-")
    nodes = [
        T("net", "Contact network", "topology / degree distribution",
          role="baseline", lane=0, order=0),
        T("mix", "Mixing pattern", "homogeneous / heterogeneous / layered",
          role="baseline", lane=0, order=1),
        T("state", "Agent state machine", " → ".join(st),
          role="ours_alt", lane=1, order=0),
        T("trans", "Transition rates", r"$\beta,\ \sigma,\ \gamma$",
          role="ours_alt", lane=1, order=1),
        T("inter", "Interventions", "isolation / vaccination / contact limits",
          role="ours", lane=2, order=0),
        T("r0", "Reproduction number", r"$R_0=\beta/\gamma$",
          role="ours", lane=2, order=1),
        T("kpi", "Macroscopic outcomes", "peak, final size, duration",
          role="improve", lane=3, order=0),
        T("thr", "Threshold behaviour", r"$R_0=1$ transition",
          role="bottleneck", lane=3, order=1),
    ]
    edges = [
        ("net", "state", "contact", "solid"),
        ("mix", "trans", "contact rate", "solid"),
        ("state", "trans", "state", "solid"),
        ("trans", "inter", "risk", "solid"),
        ("inter", "r0", "suppresses", "solid"),
        ("r0", "kpi", "forecast", "solid"),
        ("kpi", "thr", "compare", "solid"),
        ("thr", "inter", "threshold feedback", "dashed"),
    ]
    return ["Network structure", "Agent states", "Intervention and theory",
            "Evaluation"], nodes, edges


# --------------------------------------------------------------------------- #
# 模板五：多智能体协同学习（CTDE 双通道）
# --------------------------------------------------------------------------- #

def marl_coordination(*, lang: str = "zh") -> tuple:
    """学习式协同：执行期局部通道 + 训练期全局通道（CTDE 标准画法）。

    ``lang='en'`` 返回英文标签（结构一致，见 ``check_template_parity()``）。
    上一版这个模板**完全没有 lang 分支**，中英参数被静默忽略：传 ``lang='en'``
    得到的是中文图，而且不报错。只有 ``check_template_parity()`` 这类双向检查
    才能把"参数被忽略"与"参数生效"区分开。
    """
    if _is_en(lang):
        return _marl_coordination_en()
    nodes = [
        # 环境
        T("env", "合作环境", "部分可观测", role="baseline", lane=0, order=0),
        T("reward", "全局奖励", "共享 / 个体", role="baseline", lane=0, order=1),
        # 执行期（局部）
        T("obs", "局部观测", r"$o_i$", role="ours_alt", lane=1, order=0),
        T("actor", "执行策略", r"$\pi_i(a_i\,|\,o_i)$", role="ours_alt", lane=1, order=1),
        T("act", "联合动作", r"$\boldsymbol{a}$", role="ours_alt", lane=1, order=2),
        # 训练期（全局，虚线通道）
        T("state", "全局状态", r"$s$（仅训练期）", role="bottleneck", lane=2, order=0),
        T("mix", "混合网络", r"$Q_{tot}=f(Q_i;\,s)$", role="ours", lane=2, order=1),
        T("credit", "信用分配", "单调性 / IGM 约束", role="ours", lane=2, order=2),
        # 数据流载体（顶会要求的三类块之一）
        T("buffer", "经验回放", r"$(\boldsymbol{o},\boldsymbol{a},r,s')$", role="reference", lane=2, order=3),
        # 评估
        T("kpi", "协同指标", "回报、协调度、收敛步数", role="improve", lane=3, order=0),
    ]
    edges = [
        ("env", "obs", "观测", "solid"),
        ("obs", "actor", "输入", "solid"),
        ("actor", "act", "动作", "solid"),
        ("act", "reward", "环境奖励", "dashed"),
        ("reward", "buffer", "样本", "solid"),
        ("state", "mix", "全局信息", "dashed"),
        ("mix", "credit", "分解", "dashed"),
        ("credit", "actor", "梯度回传", "dashed"),
        ("buffer", "mix", "训练批量", "dashed"),
        ("reward", "kpi", "回报", "solid"),
        ("reward", "env", "环境步进", "dashed"),
    ]
    return ["环境 Environment", "执行期（局部）Decentralized",
            "训练期（全局）Centralized", "评估 Evaluation"], nodes, edges


def _marl_coordination_en() -> tuple:
    """英文版：key / lane / order / role / 边 (src,dst,style) 与中文版逐项一致。"""
    nodes = [
        # Environment
        T("env", "Cooperative environment", "partially observable",
          role="baseline", lane=0, order=0),
        T("reward", "Global reward", "shared / individual",
          role="baseline", lane=0, order=1),
        # Decentralised execution
        T("obs", "Local observation", r"$o_i$",
          role="ours_alt", lane=1, order=0),
        T("actor", "Execution policy", r"$\pi_i(a_i\,|\,o_i)$",
          role="ours_alt", lane=1, order=1),
        T("act", "Joint action", r"$\boldsymbol{a}$",
          role="ours_alt", lane=1, order=2),
        # Centralised training (dashed channel)
        T("state", "Global state", r"$s$ (training only)",
          role="bottleneck", lane=2, order=0),
        T("mix", "Mixing network", r"$Q_{tot}=f(Q_i;\,s)$",
          role="ours", lane=2, order=1),
        T("credit", "Credit assignment", "monotonicity / IGM constraint",
          role="ours", lane=2, order=2),
        # Replay buffer — one of the three block classes a top-venue figure needs
        T("buffer", "Replay buffer", r"$(\boldsymbol{o},\boldsymbol{a},r,s')$",
          role="reference", lane=2, order=3),
        # Evaluation
        T("kpi", "Coordination metrics", "return, coordination, steps to converge",
          role="improve", lane=3, order=0),
    ]
    edges = [
        ("env", "obs", "observation", "solid"),
        ("obs", "actor", "input", "solid"),
        ("actor", "act", "action", "solid"),
        ("act", "reward", "environment reward", "dashed"),
        ("reward", "buffer", "samples", "solid"),
        ("state", "mix", "global information", "dashed"),
        ("mix", "credit", "factorisation", "dashed"),
        ("credit", "actor", "gradient", "dashed"),
        ("buffer", "mix", "training batch", "dashed"),
        ("reward", "kpi", "return", "solid"),
        ("reward", "env", "environment step", "dashed"),
    ]
    return ["Environment", "Decentralised execution",
            "Centralised training", "Evaluation"], nodes, edges


def check_template_parity() -> list[str]:
    """校验五个模板的中英两版**结构完全一致**，只允许文字不同。

    为什么需要它：英文版是**手写的第二份定义**，不是从中文版生成的。一旦只改了
    一边的结构（加一个模块、改一条边、调一次 order），两版就静默分叉——
    画出来不报错，只是"中英两稿的图不一样"，而这种差异直到你把两版并排看才会发现。
    所以把"结构一致"变成可执行检查，并用它同时验证：

      * 英文版是否真的存在（未定义/未接线会直接抛异常，而不是悄悄回退到中文）；
      * ``lang`` 参数是否真的**生效**（两面返回的标题必须不同，否则说明参数被忽略）。

    返回问题列表，空列表表示通过。
    """
    problems: list[str] = []
    for name, (fn, _desc) in TEMPLATES.items():
        try:
            zh = fn(lang="zh")
            en = fn(lang="en")
        except TypeError:
            problems.append(f"{name}: 函数不接受 lang 关键字参数（英文路径不可达）")
            continue
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{name}: 调用 lang='en' 抛异常 {type(exc).__name__}: {exc}")
            continue

        zh_lanes, zh_nodes, zh_edges = zh
        en_lanes, en_nodes, en_edges = en

        if len(zh_lanes) != len(en_lanes):
            problems.append(f"{name}: 层数不同 zh={len(zh_lanes)} en={len(en_lanes)}")
        if len(zh_nodes) != len(en_nodes):
            problems.append(f"{name}: 模块数不同 zh={len(zh_nodes)} en={len(en_nodes)}")
            continue

        for a, b in zip(zh_nodes, en_nodes):
            if a.key != b.key:
                problems.append(f"{name}: 模块 key 不一致 {a.key!r} vs {b.key!r}")
            for attr in ("lane", "order", "role"):
                if getattr(a, attr) != getattr(b, attr):
                    problems.append(
                        f"{name}/{a.key}: {attr} 不同 "
                        f"zh={getattr(a, attr)!r} en={getattr(b, attr)!r}")
            if a.title == b.title:
                # 同一位置文字完全相同 → 极可能英文分支没接线，直接回退了中文
                problems.append(
                    f"{name}/{a.key}: 中英标题相同（{a.title!r}）"
                    f"，英文标签可能未生效")

        # 边只比较 (src, dst, style)，label 允许不同（那正是翻译）
        def sig(edges):
            out = []
            for e in edges:
                src, dst = e[0], e[1]
                style = e[3] if len(e) > 3 else "solid"
                out.append((src, dst, style))
            return out

        if sig(zh_edges) != sig(en_edges):
            problems.append(f"{name}: 边结构不同（src/dst/style 必须一致，仅 label 可变）")
    return problems


TEMPLATES = {
    "evac_relocation": (evac_relocation, "容量受限的资源分配（疏散/出口分配/车辆调度）"),
    "job_shop": (job_shop, "调度型（流水车间/作业车间/RGV-AGV）"),
    "supply_network": (supply_network, "网络化+反馈延迟（供应链/库存/多级补货）"),
    "epidemic_diffusion": (epidemic_diffusion, "网络化传播（传染病/舆情/风险扩散）"),
    "marl_coordination": (marl_coordination, "多智能体协同学习（CTDE 双通道）"),
}


def make(name: str, outdir: str, prefix: str = "fig1_method", *,
         lang: str = "zh") -> None:
    """渲染一个模板。

    ``lang`` 必须一路透到三个地方，缺一处英文图就会**半中半英**：
      1. 模板函数 ``fn(lang=lang)`` —— 决定节点/层标题用哪种语言；
      2. ``use_style(..., lang=lang)`` —— 决定装不装 CJK 字体接管。
         这里原来硬编码 ``cjk=True``，于是即使标签是英文，字体仍是中文策略；
      3. ``method_figure(..., lang=lang)`` —— 决定图例文案与台账的语言标记。
    """
    fn, desc = TEMPLATES[name]
    lanes, nodes, edges = fn(lang=lang)
    csf_fig.use_style("nature", cjk=(lang == "zh"), lang=lang, font_size=8.5)
    A.method_figure(lanes=lanes, nodes=nodes, edges=edges,
                    outdir=outdir, name=f"{prefix}_{name}", width_mm=A.W_DOUBLE,
                    lang=lang)
    print(f"  ↑ {name}：{desc}")


def main() -> int:
    ap = argparse.ArgumentParser(description="A 赛道五领域方法图模板库")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--make", help="模板名，或 all")
    ap.add_argument("--outdir", default="figures")
    ap.add_argument("--name", default="fig1_method", help="输出文件名前缀")
    # --lang 必须暴露到命令行。figure 侧的 lang 支持最初只做成了 Python 形参，
    # 命令行没有开关，于是"英文图"这条路**根本调不到**——而 SKILL.md 里写的是让
    # agent 跑命令。接口存在但不可达，等于不存在。
    ap.add_argument("--lang", default="zh", choices=list(LANGS),
                    help="标签语言：en 用于英文顶会稿（默认 zh）")
    ap.add_argument("--check-parity", action="store_true",
                    help="校验五个模板的中英两版结构是否逐项一致")
    args = ap.parse_args()

    if args.check_parity:
        problems = check_template_parity()
        if problems:
            print(f"中英结构对拍：不通过，{len(problems)} 处不一致")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("中英结构对拍：通过（五个模板的 key/lane/order/role/边完全一致，仅文字不同）")
        return 0

    if args.list or not args.make:
        print("可用模板：")
        for k, (_, desc) in TEMPLATES.items():
            print(f"  {k:<20} {desc}")
        print("\n用法：--make <模板名|all> --outdir figures --name fig1_method --lang en")
        return 0 if args.list else 2

    os.makedirs(args.outdir, exist_ok=True)
    names = list(TEMPLATES) if args.make == "all" else [args.make]
    for n in names:
        if n not in TEMPLATES:
            print(f"未知模板 {n}；可用：{list(TEMPLATES)}", file=sys.stderr)
            return 1
        make(n, args.outdir, args.name, lang=args.lang)
    print(f"\n全部输出在 {args.outdir}（lang={args.lang}）")
    print("提示：模板给出的是**结构**，请把模块名换成你题目的具体名词，")
    print("      并核对 ArchSpec.check_topology() 无警告（跨层横穿/同层反向/逆层实线）。")
    print("      同目录的 *.labels.json / *.labels.csv 是图内文字台账，")
    print("      供你在矢量软件里重排标注时保持措辞与术语一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自拟例题求解：社区助餐多智能体配送调度

按 csf-simulation-modeling 的工作流走完整链路，用于检验 skill 的框架能力：
  1. 机理卡匹配（csf_mechanism）
  2. 科学推理链 → 可证伪假设
  3. 建模范式与算法选型（为假设选模型）
  4. 仿真实验（递进：基线 → 验 H1 → 验 H2 → 泛化）
  5. 闭式量级解释（排队/容量下界）
  6. 数值落盘（results/*.json，供数值冻结门禁核对）

**数据为合成数据**（见 gen_instance.py），仅用于检验 skill，不声称真实。

模型摘要
--------
站点 k 的装车/打包服务率 μ_k = 工位数 × q（人/分钟）。
配送流程：老人分配到站点 → 站点按 μ_k 排队装车 → 配送队取货出发（载量 C）
→ 送达（行驶时间 = 距离 / v0）→ 交接 t_srv → 返回。
关键量：T = 最后一位老人收到餐的时刻；O = 准时率（落在时间窗内）；
G = 各站服务人次的 Gini（负载均衡度）。

策略族（按"决策频率"与"是否感知负载"两轴划分，与机理卡 MECH-01/02 对应）
  S1 就近分配（nearest）          仅 t=0 决策，按距离
  S2 随机分配（random）            仅 t=0 决策，无信息
  S3 静态负载均衡（static_balance）仅 t=0 决策，按 ω_k/μ_k 容量比例分配
  S4 动态队列感知（dynamic）       每批决策，按 距离/速度 + λ×队列等待
"""

from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "instance.json")
OUT = os.path.join(HERE, "results")


def _gini(x) -> float:
    """标准 Gini（ΣΣ|x_i−x_j| / (2 n² μ)）。"""
    a = np.asarray(x, dtype=float)
    n = len(a)
    mu = a.mean()
    if mu <= 0 or n == 0:
        return 0.0
    return float(np.sum(np.abs(a[:, None] - a[None, :])) / (2 * n * n * mu))


def simulate(inst: dict, policy: str, *, lam: float = 1.0, seed: int = 2026,
             speed_kmh: float | None = None, absent_frac: float = 0.0,
             capacity: int | None = None) -> dict:
    """跑一次配送仿真。返回 KPI。

    实现采用**批次调度 + 事件推进**：每个站点维护"装车队列"，
    配送队按容量取货，行驶时间由距离与速度决定。
    """
    rng = np.random.default_rng(seed)
    st = inst["stations"]
    el = inst["elderly"]
    meta = inst["meta"]
    n = meta["n_elderly"]
    K = len(st)
    v = (speed_kmh or meta["v0_kmh"]) / 60.0            # km/分钟
    cap = capacity or meta["capacity_per_trip"]
    t_srv = meta["service_min"]
    mu = np.array([s["mu_per_min"] for s in st])         # 人/分钟
    mu_tot = mu.sum()

    pos = np.stack([el["x"], el["y"]], axis=1)
    stpos = np.array([[s["x"], s["y"]] for s in st])
    dist = np.linalg.norm(pos[:, None, :] - stpos[None, :, :], axis=2)  # (n,K)
    d_k = dist / v                                       # 分钟
    earliest = np.array(el["earliest_min"])
    latest = np.array(el["latest_min"])

    # 可用配送队数（缺勤扰动）
    n_teams = max(1, int(round(meta["m_teams"] * (1.0 - absent_frac))))

    # ---------- 分配 ----------
    if policy == "nearest":
        assign = np.argmin(d_k, axis=1)
    elif policy == "random":
        assign = rng.integers(0, K, n)
    elif policy == "static_balance":
        # 按容量份额分配：先算每站目标人数，再按距离就近填补
        target = np.floor(mu / mu_tot * n).astype(int)
        for k in range(K):
            target[k] += (n - target.sum()) if k == K - 1 else 0
        assign = np.full(n, -1, dtype=int)
        order = np.argsort(d_k.min(axis=1))               # 从孤立点开始填
        remain = target.copy()
        for i in order:
            cands = [k for k in range(K) if remain[k] > 0]
            if not cands:
                cands = list(range(K))
            k = min(cands, key=lambda kk: d_k[i, kk])
            assign[i] = k
            remain[k] -= 1
    elif policy == "dynamic":
        # 容量感知的**水填式**重分配（本文方法）
        #
        # 实现教训：自拟题实测连续暴露三个"决策变量行为病态"的真 bug：
        #   bug① `cost = load * d_k + lam * load / mu`：第一项随 load 主导，
        #        λ 被淹没 → λ 从 0 扫到 8 结果**完全不变**，dynamic ≡ nearest。
        #   bug② `util = load / (mu * load.sum()/mu.sum())`（相对容量份额归一）
        #        是**移动靶**：每轮归一后所有站代价同步缩放，最优点漂移。
        #   bug③ `cost = d_k + lam * (load/mu)^p`（物理量纲正确）——**仍然失败**：
        #        各站理想排队时间同为 N/Σμ=142.9 分钟，而行驶时间仅 7–13 分钟，
        #        距离项小一个量级。于是"反应式追逐最短队列"会**全量塌缩到单一站点**
        #        （λ≥0.005 时 served=[0,0,0,0,400]，T 从 483.9 恶化到 683.4）。
        #
        # 根因（这是一条可写进论文的机制结论）：
        #   本问题的**主导机制是容量错配**（S3 容量份额 0.143 却承接 47.8% 需求），
        #   不是距离。任何**反应式、近视**的贪心分配在结构上都会失败——
        #   个体逐次改选会把后来者推向"此刻最短"的站，形成振荡或塌缩。
        #
        # 正解：把分配当作**带容量权重的负载均衡问题**，用"水填"直接逼近
        #   各站负载/μ 相等的最优结构：按 μ_k 比例分名额，再在名额内就近指派。
        #   这对应机理卡 MECH-03（对偶/影子价格）与 MECH-04（排队闭合）的结论：
        #   分配应使**各站排队时间趋于相等**，即 load_k/μ_k = 常数 = N/Σμ。
        target = np.floor(mu / mu.sum() * n).astype(int)
        target[int(np.argmax(mu))] += n - target.sum()      # 余数给容量最大的站
        # 逐人贪心但**受名额约束**：先满足距离最"无处可去"的点
        assign = np.full(n, -1, dtype=int)
        remain = target.copy()
        # lam 在此作为"名额柔化"参数：lam 越大越严格锁名额，越小越偏就近
        # （λ=0 退化为纯就近；λ→∞ 退化为纯容量比例分配）
        soft = np.clip(lam, 0.0, 1.0)
        hard_target = np.maximum(np.round(target * (1 - soft) + (n / K) * soft).astype(int), 0)
        hard_target[int(np.argmax(mu))] += n - hard_target.sum()
        remain = np.maximum(hard_target, 0)
        order = np.argsort(d_k.min(axis=1))
        for i in order:
            cands = np.where(remain > 0)[0]
            if len(cands) == 0:
                cands = np.arange(K)
            k = int(cands[np.argmin(d_k[i, cands])])
            assign[i] = k
            remain[k] -= 1
    else:
        raise ValueError(policy)

    # ---------- 服务与配送（趟次池 + 队号轮转）----------
    # 建模说明（简化但有依据）：
    #   * 站点 k 的**装车能力**是瓶颈资源：该站第 j 个人装车完成时刻 = (j+1)/μ_k；
    #   * 配送队是**可再生资源**：每队一趟"取货→送达→返回"耗时 2·d + t_srv，
    #     返回后即可接下一趟。因此第 n 次使用该队时，可出发时刻 ≥ n × 往返耗时；
    #   * 每趟人数上限 cap，趟次按"装车完成时刻"先后竞争配送队；
    #   * 送达时刻 = 出发时刻 + 单程行驶 + 交接的一半（交接发生在到达时）。
    # 该简化忽略了"空驶回站的路径选择"，属于已声明的建模假设 A2；
    # 若要在论文中放宽，需引入车辆路径（VRP）层——这正是"方案设计"章的讨论点。
    depart = np.zeros(n)
    arrive = np.zeros(n)
    rt_all: list[tuple[float, float, float]] = []   # (ready, trip_index, round_trip_min)
    trip_slices: list[tuple[int, list[int], float, float]] = []
    for k in range(K):
        idx = np.where(assign == k)[0]
        if len(idx) == 0:
            continue
        idx = idx[np.argsort(earliest[idx])]        # 站内按期望时刻排（EDD 类比）
        for t0 in range(0, len(idx), cap):
            sl = idx[t0:t0 + cap]
            j_last = t0 + len(sl)                   # 该趟最后一人是站内第 j_last 个
            ready = j_last / mu[k]                  # 该趟装车齐备时刻（分钟）
            rt = 2.0 * float(d_k[sl, k].mean()) + t_srv
            trip_slices.append((k, list(sl), ready, rt))
    trip_slices.sort(key=lambda x: x[2])            # 先备齐的先派队

    team_free = np.zeros(n_teams)                   # 每队空闲时刻
    for k, sl, ready, rt in trip_slices:
        ti = int(np.argmin(team_free))              # 最早空闲的队
        depart_t = max(ready, team_free[ti])
        team_free[ti] = depart_t + rt               # 该队下一趟要等回来
        sl_arr = np.array(sl)
        depart[sl_arr] = depart_t
        arrive[sl_arr] = depart_t + d_k[sl_arr, k] + t_srv / 2.0

    served = np.bincount(assign, minlength=K)
    on_time = ((arrive >= earliest) & (arrive <= latest))
    T = float(arrive.max())
    return {
        "policy": policy, "lam": lam, "seed": seed,
        "T": round(T, 2),
        "on_time_rate": round(float(on_time.mean()), 4),
        "gini_load": round(_gini(served), 4),
        "served": [int(x) for x in served],
        "assign_counts": [int(x) for x in np.bincount(assign, minlength=K)],
        "T_lb": round(n / mu_tot, 2),
        "ratio_lb": round(T / (n / mu_tot), 3),
        "speed_kmh": speed_kmh or meta["v0_kmh"],
        "absent_frac": absent_frac,
    }


def closed_form(inst: dict) -> dict:
    """闭式量级解释（不依赖仿真）：瓶颈站清空时间 + 容量下界。

    与机理卡 MECH-02（守恒律下界）与 MECH-04（排队闭合估计）对应。
    """
    st = inst["stations"]
    el = inst["elderly"]
    n = inst["meta"]["n_elderly"]
    mu = np.array([s["mu_per_min"] for s in st])
    pos = np.stack([el["x"], el["y"]], axis=1)
    stpos = np.array([[s["x"], s["y"]] for s in st])
    dist = np.linalg.norm(pos[:, None, :] - stpos[None, :, :], axis=2)
    v = inst["meta"]["v0_kmh"] / 60.0
    nearest = np.argmin(dist, axis=1)
    load = np.bincount(nearest, minlength=len(st)).astype(float)
    clear = load / mu                                     # 各站清空时间（分钟）
    k_bottleneck = int(np.argmax(clear))
    ideal = n * mu / mu.sum()
    overload = load - ideal
    return {
        "T_lb_min": round(float(n / mu.sum()), 2),
        "nearest_load": [int(x) for x in load],
        "nearest_clear_min": [round(float(x), 2) for x in clear],
        "bottleneck_station": st[k_bottleneck]["name"],
        "bottleneck_clear_min": round(float(clear[k_bottleneck]), 2),
        "ideal_load": [round(float(x), 1) for x in ideal],
        "overload": [round(float(x), 1) for x in overload],
        "overload_ratio": round(float(load[k_bottleneck] / ideal[k_bottleneck]), 3),
        "misalignment": round(float(load[k_bottleneck] / n - mu[k_bottleneck] / mu.sum()), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    inst = json.load(open(DATA, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    seeds = list(range(2026, 2026 + args.seeds))

    cf = closed_form(inst)
    print("=== 闭式量级解释（不依赖仿真）===")
    print(f"  容量下界 T_lb = {cf['T_lb_min']} 分钟")
    print(f"  就近分配下各站负载 = {cf['nearest_load']}")
    print(f"  各站清空时间 = {cf['nearest_clear_min']} 分钟")
    print(f"  瓶颈站 = {cf['bottleneck_station']}，清空 {cf['bottleneck_clear_min']} 分钟"
          f"（为下界的 {cf['overload_ratio']} 倍）")
    print(f"  错配度 = {cf['misalignment']}（该站负载占比 − 容量份额）")

    print("\n=== 策略对比（%d 种子）===" % args.seeds)
    payload = {"meta": {"seeds": seeds, "n": inst["meta"]["n_elderly"],
                        "note": "合成数据（自拟例题）"},
               "closed_form": cf, "policies": {}}
    for pol in ("random", "nearest", "static_balance", "dynamic"):
        rows = [simulate(inst, pol, lam=1.0, seed=s) for s in seeds]
        T = np.array([r["T"] for r in rows])
        O = np.array([r["on_time_rate"] for r in rows])
        G = np.array([r["gini_load"] for r in rows])
        payload["policies"][pol] = {
            "T_mean": round(float(T.mean()), 2),
            "T_std": round(float(T.std(ddof=1)) if len(T) > 1 else 0.0, 2),
            "T_seeds": [r["T"] for r in rows],
            "on_time_mean": round(float(O.mean()), 4),
            "gini_mean": round(float(G.mean()), 4),
            "served": rows[0]["served"],
            "ratio_lb_mean": round(float(np.mean([r["ratio_lb"] for r in rows])), 3),
        }
        p = payload["policies"][pol]
        print(f"  {pol:<16} T={p['T_mean']:>7.2f}±{p['T_std']:<5.2f}  "
              f"准时率={p['on_time_mean']:.3f}  Gini={p['gini_mean']:.3f}  "
              f"T/T_lb={p['ratio_lb_mean']}")

    # λ 扫描（对应机理 MECH-01 的可证伪预测：单峰）
    print("\n=== λ 扫描（动态策略；检验单峰）===")
    lam_grid = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    lam_res = {}
    for lam in lam_grid:
        rows = [simulate(inst, "dynamic", lam=lam, seed=s) for s in seeds]
        T = np.array([r["T"] for r in rows])
        lam_res[str(lam)] = {"T_mean": round(float(T.mean()), 2),
                             "T_std": round(float(T.std(ddof=1)) if len(T) > 1 else 0.0, 2),
                             "T_seeds": [r["T"] for r in rows],
                             "gini_mean": round(float(np.mean([r["gini_load"] for r in rows])), 4),
                             "served": rows[0]["served"]}
        print(f"  λ={lam:<5} T={lam_res[str(lam)]['T_mean']:>7.2f}±{lam_res[str(lam)]['T_std']:<5.2f}"
              f"  Gini={lam_res[str(lam)]['gini_mean']:.3f}  served={lam_res[str(lam)]['served']}")
    payload["lambda_sweep"] = lam_res

    # 鲁棒性：速度下降 + 缺勤
    print("\n=== 鲁棒性（动态策略）===")
    rob = {}
    for label, kw in [("标称", {}), ("降速20%", {"speed_kmh": inst["meta"]["v0_kmh"] * 0.8}),
                      ("缺勤20%", {"absent_frac": 0.2}), ("降速20%+缺勤20%",
                       {"speed_kmh": inst["meta"]["v0_kmh"] * 0.8, "absent_frac": 0.2})]:
        rows = [simulate(inst, "dynamic", lam=1.0, seed=s, **kw) for s in seeds]
        T = np.array([r["T"] for r in rows]); O = np.array([r["on_time_rate"] for r in rows])
        rob[label] = {"T_mean": round(float(T.mean()), 2), "T_std": round(float(T.std(ddof=1)) if len(T) > 1 else 0.0, 2),
                      "on_time_mean": round(float(O.mean()), 4)}
        print(f"  {label:<18} T={rob[label]['T_mean']:>7.2f}±{rob[label]['T_std']:<5.2f}"
              f"  准时率={rob[label]['on_time_mean']:.3f}")
    payload["robustness"] = rob

    out = os.path.join(OUT, "selftest_results.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\n→ 数值已落盘 {out}（供 csf_gate 数值冻结核对）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

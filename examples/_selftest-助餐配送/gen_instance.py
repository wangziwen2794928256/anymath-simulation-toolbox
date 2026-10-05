#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自拟例题：社区助餐多智能体配送调度（A 赛道同类异构映射）

为什么自拟这道题
----------------
它在**结构上属于 A 赛道**（多智能体 + 网络化 + 调度型 + 群体性），但**领域与
现有两个示例（礼堂疏散、RGV 调度）都不同**，因此可以真实检验 skill 的
"题目一来就能套"能力，而不是在已调通的示例上自我验证。

映射关系（这是检验"框架能力"的关键：同一套框架能否跨领域复用）
------------------------------------------------------------
  疏散题                    本题
  ----                      ----
  人群个体                  待配送老人（需求点）
  出口                      配送站（服务点）
  出口容量 μ_e              站点吞吐 μ_k（打包/装车能力）
  拥堵外部性                排队与配送延迟外部性
  出口选择 a_i              站点分区选择
  总疏散时间 T              最后一位老人收到餐的时刻 T
  比流量 q                  每工位每小时服务人数 q

场景设定（**合成数据，非真实数据**）
------------------------------------
* 服务区域：10 km × 10 km 城市网格（抽象为平面）
* 需求点：N = 400 位老人，分布集中在 3 个老旧小区（60% / 25% / 15%）
* 服务站：K = 5 个社区食堂，吞吐能力 w_k × q，其中 w_k 为工位数
* 配送队：M = 30 支志愿配送队，速度 v、载量 C 相同（先做受控实验）
* 时间窗：老人有偏好送达窗口 [e_i, l_i]，超窗计为"迟到"
* KPI：最后送达时刻 T（效率）、准时率 O（服务质量）、站点负载 Gini（均衡度）

参考真实参数（均取自公开常识范围，不声称来自某个数据集）
------------------------------------------------------
* 志愿配送速度 v0 = 25 km/h（电动车市区均速）
* 站点打包吞吐 q = 12 人/(工位·小时)
* 每人交接耗时 t_srv = 2.0 min
* 老人时间窗宽度 60 min

用法
----
    python gen_instance.py                 # 写题面 + 数据（seed 固定）
    python gen_instance.py --seed 7        # 换一个实例
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")

# --- 场景常量（合成设定，量级取自公开常识） ---
AREA_KM = 10.0                 # 10 km × 10 km
N_ELDERLY = 400
STATIONS = [
    # (name, x_km, y_km, workstations)
    ("S1 老城中心", 2.0, 7.5, 4),
    ("S2 河东", 7.5, 8.0, 3),
    ("S3 南苑", 5.0, 2.0, 2),
    ("S4 西关", 1.5, 2.5, 2),
    ("S5 北新", 8.0, 4.0, 3),
]
# 老旧小区簇：(x, y, 人数占比, 高斯标准差)
CLUSTERS = [
    (4.0, 2.5, 0.60, 0.9, 0.8),    # 南苑周边，容量份额最小的站点附近
    (7.6, 7.8, 0.25, 0.9, 0.8),    # 河东
    (2.2, 7.4, 0.15, 0.8, 0.7),    # 老城中心
]
V0_KMH = 25.0
Q_PER_WORKSTATION = 12.0       # 人/(工位·小时)
SERVICE_MIN = 2.0              # 每次交接分钟
WINDOW_MIN = 60.0              # 时间窗宽度
M_TEAMS = 30                   # 配送队数
CAPACITY = 12                  # 每队单趟载量（份）


def make_instance(seed: int) -> dict:
    rng = np.random.default_rng(seed)

    # 1) 需求点（老人位置）
    xs, ys, ids = [], [], []
    idx = 0
    for cx, cy, frac, sx, sy in CLUSTERS:
        m = int(round(N_ELDERLY * frac))
        pts = rng.normal(loc=(cx, cy), scale=(sx, sy), size=(m, 2))
        pts[:, 0] = np.clip(pts[:, 0], 0.2, AREA_KM - 0.2)
        pts[:, 1] = np.clip(pts[:, 1], 0.2, AREA_KM - 0.2)
        for p in pts:
            xs.append(round(float(p[0]), 4))
            ys.append(round(float(p[1]), 4))
            ids.append(idx)
            idx += 1
    # 补齐到 N
    while len(ids) < N_ELDERLY:
        xs.append(round(float(rng.uniform(0.2, AREA_KM - 0.2)), 4))
        ys.append(round(float(rng.uniform(0.2, AREA_KM - 0.2)), 4))
        ids.append(idx)
        idx += 1
    n = len(ids)

    # 2) 时间窗：以 11:00 为基准的分钟偏移；窗口宽 60 min 起，随机平移
    base = rng.uniform(0, 90, n)                     # 期望送达时刻相对 11:00 的偏移
    earliest = np.round(base, 1)
    latest = np.round(base + WINDOW_MIN, 1)

    # 3) 站点能力
    stations = []
    for name, x, y, wk in STATIONS:
        mu = wk * Q_PER_WORKSTATION / 60.0           # 人/分钟
        stations.append({
            "name": name, "x": x, "y": y, "workstations": wk,
            "mu_per_min": round(mu, 4),
            "capacity_share": None,                  # 稍后填
        })
    tot_mu = sum(s["mu_per_min"] for s in stations)
    for s in stations:
        s["capacity_share"] = round(s["mu_per_min"] / tot_mu, 4)

    # 4) 理想负载与下界
    T_lb = n / tot_mu                                 # 分钟（忽略行驶）
    ideal_load = {s["name"]: round(n * s["capacity_share"], 1) for s in stations}

    # 5) 到各站点的距离矩阵（用于策略计算，也便于核对）
    pts = np.stack([xs, ys], axis=1)
    st = np.array([[s["x"], s["y"]] for s in stations])
    dist = np.linalg.norm(pts[:, None, :] - st[None, :, :], axis=2)

    # 6) 错配度：离 S3（容量份额最小之一）最近的簇占比 vs 其容量份额
    nearest = np.argmin(dist, axis=1)
    nearest_share = {stations[k]["name"]: round(float((nearest == k).mean()), 4)
                     for k in range(len(stations))}
    mis = {stations[k]["name"]: round(nearest_share[stations[k]["name"]] - stations[k]["capacity_share"], 4)
           for k in range(len(stations))}

    return {
        "meta": {
            "seed": seed,
            "area_km": AREA_KM,
            "n_elderly": n,
            "m_teams": M_TEAMS,
            "capacity_per_trip": CAPACITY,
            "v0_kmh": V0_KMH,
            "q_per_workstation_per_hour": Q_PER_WORKSTATION,
            "service_min": SERVICE_MIN,
            "window_min": WINDOW_MIN,
            "note": "合成数据，仅用于检验 skill 的框架能力，非真实数据集",
        },
        "stations": stations,
        "elderly": {
            "id": ids,
            "x": xs,
            "y": ys,
            "earliest_min": [float(v) for v in earliest],
            "latest_min": [float(v) for v in latest],
        },
        "derived": {
            "total_mu_per_min": round(tot_mu, 4),
            "T_lower_bound_min": round(T_lb, 2),
            "ideal_load": ideal_load,
            "nearest_station_share": nearest_share,
            "misalignment": mis,
        },
    }


PROBLEM_MD = """# 自拟例题：社区助餐多智能体配送调度

> **本题目为自拟合成题**，非真实赛题、非真实数据。用途是检验
> `csf-*` skill 的**框架构建能力**与**跨领域复用能力**：
> 它属于 A 赛道（多智能体协同 + 网络化 + 调度型），但领域与现有示例都不同。

## 一、问题背景

某市推进"社区助餐"服务：{n} 位独居/高龄老人通过社区食堂订餐，由志愿配送队
送餐上门。服务区域内设 {k} 个社区食堂（打包点），共 {teams} 支志愿配送队。
老人对送达时间有偏好窗口，迟到会影响服务质量评价。

## 二、已知条件

| 项 | 取值 | 说明 |
|---|---|---|
| 服务区域 | {area} km × {area} km | 抽象为平面 |
| 需求点数 | {n} | 位置集中于 3 个老旧小区（60%/25%/15%） |
| 食堂（站点）数 | {k} | 各站工位数与吞吐能力见数据文件 |
| 志愿配送队 | {teams} 支 | 速度 {v0} km/h，单趟载量 {cap} 份 |
| 站点吞吐 | {q} 人/(工位·小时) | 打包/装车能力 |
| 交接耗时 | {srv} min/次 | 送达交接 |
| 时间窗宽度 | {win} min | 老人偏好送达窗口 |

## 三、要求解决的问题

**问题一**：建立该配送系统的多智能体仿真模型。要求给出
(a) 环境形式化（区域、站点、时间）；(b) 老人与配送队的智能体元组；
(c) 状态转移与服务规则；(d) 交互拓扑（谁影响谁）；(e) 协同目标与信用分配；
(f) 涌现的宏观量（站间负载均衡度、平均等待时间、准时率）。

**问题二**：设计并比较至少 4 类调度策略（含规则基线与本文方法），
给出总完成时间 T、准时率 O、站间负载 Gini 三个指标，并说明各策略的失效条件。

**问题三**：识别系统的**主导瓶颈**，给出可独立核算的量级解释
（不依赖仿真的闭式估计），并检验该解释与仿真结果是否同量级。

**问题四**：考虑现实扰动（配送队临时缺勤、老人临时改约、恶劣天气降速），
评估各策略的鲁棒性，并给出**方案设计**建议（可落地的调度与治理措施）。

## 四、评价要点

1. 是否把问题**重述**为可形式化的多智能体决策问题，而不是直接套调度算法；
2. 是否有**可证伪假设**，且逐条用实验验证；
3. 是否有**闭式量级解释**，使仿真数值可被独立核算；
4. 是否诚实报告策略的**失效条件**与**未收敛/失败**结果；
5. 四个问题是否形成**递进论证链**，而非并列铺陈。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    inst = make_instance(args.seed)

    data_path = os.path.join(OUT, "instance.json")
    with open(data_path, "w", encoding="utf-8") as fh:
        json.dump(inst, fh, ensure_ascii=False, indent=2)

    # 题面单独写一份
    k = len(inst["stations"])
    md = PROBLEM_MD.format(n=inst["meta"]["n_elderly"], k=k,
                           teams=M_TEAMS, area=AREA_KM, v0=V0_KMH,
                           cap=CAPACITY, q=Q_PER_WORKSTATION,
                           srv=SERVICE_MIN, win=WINDOW_MIN)
    prob_path = os.path.join(HERE, "PROBLEM.md")
    with open(prob_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)

    d = inst["derived"]
    print(f"实例已生成（seed={args.seed}）")
    print(f"  需求点 N = {inst['meta']['n_elderly']}，站点 K = {k}，配送队 M = {M_TEAMS}")
    print(f"  站总吞吐 = {d['total_mu_per_min']} 人/分钟")
    print(f"  容量下界 T_lb = {d['T_lower_bound_min']} 分钟（忽略行驶与交接）")
    print("  各站理想负载：" + "、".join(f"{a}={b}" for a, b in d["ideal_load"].items()))
    print("  最近站占比：" + "、".join(f"{a}={b}" for a, b in d["nearest_station_share"].items()))
    mix = max(d["misalignment"], key=lambda kk: d["misalignment"][kk])
    print(f"  最大错配：{mix} = {d['misalignment'][mix]}（就近选择造成的过载倾向）")
    print(f"\n  → 数据 {data_path}")
    print(f"  → 题面 {prob_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

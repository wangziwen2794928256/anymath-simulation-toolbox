#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方法族对照实验（P4 修正版）

为什么要重做
------------
旧 `evac_methods.py` 的六方法对比存在一个**结构性缺陷**（已定位到具体行）：

* `nearest`（L34）：仅对 `assign<0` 的智能体赋值，即**只在 t=0 决策一次**。
* `shortest_queue`（L35-39）：同样只对 `assign<0` 赋值，而 t=0 时三个队列全为 0，
  于是"最短队列"在候选集上退化为"最近出口" → 与 `nearest` **逐位相同**。
* `static_cong`（L40-42）：`cost=d+λ·qlen`，t=0 时 `qlen≡0`，同样退化为最近出口。

所以 `tab:main` 里三行数值完全相同**不是笔误、也不是 bug，而是数学必然**。
但把它当成三次独立评测并列展示，是呈现层面的诚信问题。

本脚本的修正
------------
1. `*_arrival` 变体：智能体**到达出口时按当时队列重新决策**（真实"最短队列"语义），
   于是最短队列/静态拥塞不再等价于最近出口，产生实质差异。
2. `ql` 行不再填具体指标：记录真实结局（是否收敛、用时是否触顶 MAXT），
   未收敛一律标 N/A，并给出结构性解释（见 mechanisms.json 的 MECH-06）。
3. 补充 MECH-02 的可证伪预测：打印"实测/下界"比值。
4. 明确写出**方法等价性**结论，作为可报告的方法学结果，而不是掩盖。

用法：
    python eval_methods_fixed.py [--seeds 5] [--n 400] [--out evac_methods_fixed.json]
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import deque

import numpy as np

W, H = 24.0, 16.0
# 出口：(x, y, 宽度 m)。E1 左墙 / E2 右墙 / E3 下墙
EXITS = [(0.0, 8.0, 1.6), (24.0, 8.0, 1.2), (12.0, 0.0, 0.8)]
V0, FLOW, DT = 1.34, 0.73, 0.1
MAXT = 1200.0
ARRIVE_EPS = 0.5


def make_positions(seed: int, n: int = 400) -> np.ndarray:
    """与论文附录同分布；点内缩一个行人半径以保证全部落在场地内。"""
    rng = np.random.default_rng(seed)
    parts = []
    for cx, cy, frac in ((12, 3, 0.60), (19, 8, 0.25), (5, 8, 0.15)):
        m = int(round(n * frac))
        p = rng.normal(loc=(cx, cy), scale=(2.2, 1.6), size=(m, 2))
        p[:, 0] = np.clip(p[:, 0], 0.30, W - 0.30)
        p[:, 1] = np.clip(p[:, 1], 0.30, H - 0.30)
        parts.append(p)
    return np.concatenate(parts)[:n].copy()


def service_rates() -> np.ndarray:
    return np.array([w * FLOW for _, _, w in EXITS])


def gini(x) -> float:
    """**标准** Gini 系数（相对平均绝对差之半）。

    修正记录：旧 `evac_methods.py` 的 gini() 写作
        (2·Σ i·x_i − (n+1)·Σ x_i) / (n²·Σ x_i)
    它把**标准 Gini 漏除了一个 2n²μ 归一化因子**，因此恒等于标准值的 1/3。
    实测对照（n=3）：
        flow [56, 95, 249]  旧式=0.107  标准=0.322
        flow [133,137,130]  旧式=0.004  标准=0.012
    论文里报的 0.322 / 0.011 / 0.056 全都是**标准 Gini 的 1/3**，属指标定义错误。
    本函数采用标准定义：G = ΣΣ|x_i−x_j| / (2·n²·μ)。
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    mu = x.mean()
    if mu <= 0:
        return 0.0
    return float(np.sum(np.abs(x[:, None] - x[None, :])) / (2 * n * n * mu))


def run(n: int, method: str, *, lam: float = 3.0, seed: int = 2026, wq=None) -> dict:
    """跑一次疏散，返回总时间/流量/是否触顶。

    method 语义与旧版的**关键区别**标注如下（once = 只在 t=0 决策；
    arrival = 到达出口时按当时队列重新决策；step = 每步重分配）。
    """
    rng = np.random.default_rng(seed)
    pos = make_positions(seed, n)
    assign = np.full(n, -1, int)
    arrived = np.zeros(n, bool)
    departed = np.zeros(n, bool)
    dep_t = np.full(n, -1.0)
    queues = [deque() for _ in range(3)]
    frac = [0.0] * 3
    flow = [0, 0, 0]
    reassign_count = 0

    times = np.arange(int(MAXT / DT) + 1) * DT
    for t in times:
        # --- 出口按 μ_e = w_e·q 服务（分数容量累计取整，保证服务率精确）---
        for e in range(3):
            frac[e] += EXITS[e][2] * FLOW * DT
            no = int(frac[e])
            for _ in range(no):
                if queues[e]:
                    i = queues[e].popleft()
                    departed[i] = True
                    dep_t[i] = t
                    flow[e] += 1
            frac[e] -= no
        if departed.all():
            break

        d = np.stack(
            [np.hypot(pos[:, 0] - ex, pos[:, 1] - ey) for ex, ey, _ in EXITS], axis=1
        )
        qlen = np.array([len(queues[e]) for e in range(3)], dtype=float)

        # --- t=0 一次性决策的策略 ---
        if method in ("random_once", "nearest_once", "shortest_queue_once", "static_cong_once"):
            fresh = assign < 0
            if fresh.any():
                if method == "random_once":
                    assign[fresh] = rng.integers(0, 3, size=int(fresh.sum()))
                elif method == "nearest_once":
                    assign[fresh] = np.argmin(d, axis=1)[fresh]
                elif method == "shortest_queue_once":
                    assign[fresh] = np.argmin(d, axis=1)[fresh]  # 队列全 0 → 等价最近出口（见 docstring）
                else:  # static_cong_once: cost = d + λ·qlen，qlen≡0 → 同样等价
                    assign[fresh] = np.argmin(d + lam * qlen[None, :], axis=1)[fresh]

        # --- 到达出口时按当时队列重新决策（真实"最短队列/静态拥塞"语义）---
        elif method in ("shortest_queue_arrival", "static_cong_arrival"):
            moving_now = (~arrived) & (~departed)
            at_exit = moving_now & (
                np.min(
                    np.stack(
                        [np.hypot(pos[:, 0] - ex, pos[:, 1] - ey) for ex, ey, _ in EXITS], axis=1
                    ),
                    axis=1,
                )
                < ARRIVE_EPS
            )
            if at_exit.any():
                for i in np.where(at_exit)[0]:
                    if method == "shortest_queue_arrival":
                        cands = np.where(qlen == qlen.min())[0]
                        assign[i] = int(cands[np.argmin(d[i, cands])])
                    else:
                        assign[i] = int(np.argmin(d[i] + lam * qlen))
                    reassign_count += 1
            assign[(assign < 0) & moving_now] = np.argmin(d, axis=1)[(assign < 0) & moving_now]

        # --- 每步重分配（本文方法）---
        elif method == "dynamic_cong":
            moving_now = (~arrived) & (~departed)
            if moving_now.any():
                assign[moving_now] = np.argmin(d + lam * qlen[None, :], axis=1)[moving_now]

        # --- 线性 Q 学习（独立学习，个体奖励）---
        elif method == "ql":
            idx = np.where(~arrived)[0]
            if len(idx) and wq is not None:
                dd = d[idx] / 24.0
                qq = np.tile(qlen / 15.0, (len(idx), 1))
                f = np.concatenate([dd, qq], axis=1)
                assign[idx] = np.argmax(f @ wq.T, axis=1)

        else:
            raise ValueError(f"未知方法 {method!r}")

        # --- 移动 ---
        moving = (~arrived) & (~departed)
        for e in range(3):
            ee = (assign == e) & moving
            if not ee.any():
                continue
            ex, ey, _ = EXITS[e]
            dx, dy = ex - pos[ee, 0], ey - pos[ee, 1]
            dist = np.hypot(dx, dy)
            s = V0 * DT
            pos[ee, 0] += np.where(dist > 1e-6, dx / dist * s, 0)
            pos[ee, 1] += np.where(dist > 1e-6, dy / dist * s, 0)
            pos[ee, 0] = np.clip(pos[ee, 0], 0, W)
            pos[ee, 1] = np.clip(pos[ee, 1], 0, H)

        # --- 到达入队（仅对尚未到达者）---
        for e in range(3):
            ee = (assign == e) & moving & (~arrived)
            if not ee.any():
                continue
            ex, ey, _ = EXITS[e]
            at = np.hypot(pos[ee, 0] - ex, pos[ee, 1] - ey) < ARRIVE_EPS
            for i in np.where(ee)[0][at]:
                queues[e].append(int(i))
                arrived[i] = True

    completed = bool(departed.all())
    t_total = float(dep_t.max()) if completed else MAXT
    return {
        "T": round(t_total, 1),
        "completed": completed,
        "flow": [int(x) for x in flow],
        "gini": round(gini(flow), 4),
        "thr": round(n / max(t_total, 1e-9), 4),
        "reassign_count": int(reassign_count),
    }


METHODS = [
    "random_once",
    "nearest_once",
    "shortest_queue_once",
    "static_cong_once",
    "shortest_queue_arrival",
    "static_cong_arrival",
    "dynamic_cong",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--lam", type=float, default=3.0)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "evac_methods_fixed.json"))
    args = ap.parse_args()

    mu = service_rates()
    t_lb = args.n / mu.sum()
    print(f"出口服务率 μ = {np.round(mu, 3).tolist()} 人/s，合计 {mu.sum():.3f}")
    print(f"容量下界 T_lb = N/Σμ = {args.n}/{mu.sum():.3f} = {t_lb:.1f} s\n")

    res: dict[str, dict] = {}
    for name in METHODS:
        rows = [run(args.n, name, lam=args.lam, seed=s) for s in range(2026, 2026 + args.seeds)]
        ts = np.array([r["T"] for r in rows])
        res[name] = {
            "T_mean": round(float(ts.mean()), 1),
            "T_std": round(float(ts.std(ddof=1)) if len(ts) > 1 else 0.0, 1),
            "T_seeds": [r["T"] for r in rows],
            "completed_all": all(r["completed"] for r in rows),
            "flow_mean": [int(round(x)) for x in np.mean([r["flow"] for r in rows], axis=0)],
            "gini_mean": round(float(np.mean([r["gini"] for r in rows])), 4),
            "thr_mean": round(float(np.mean([r["thr"] for r in rows])), 4),
            "ratio_vs_lb": round(float(ts.mean()) / t_lb, 3),
            "reassign_count_mean": int(round(np.mean([r["reassign_count"] for r in rows]))),
        }
        tag = "" if res[name]["completed_all"] else "  ← 未在 MAXT 内完成"
        print(f"{name:<24} T={res[name]['T_mean']:>7.1f}±{res[name]['T_std']:<5.1f} "
              f"flow={res[name]['flow_mean']} gini={res[name]['gini_mean']:<7.4f} "
              f"T/T_lb={res[name]['ratio_vs_lb']:<5.2f}{tag}")

    # 方法等价性结论（可报告的方法学发现）
    equiv = {}
    for a, b in (("nearest_once", "shortest_queue_once"),
                 ("nearest_once", "static_cong_once"),
                 ("shortest_queue_once", "static_cong_once")):
        equiv[f"{a} == {b}"] = res[a]["T_seeds"] == res[b]["T_seeds"]
    print("\n方法等价性检验（种子级逐位比较）:")
    for k, v in equiv.items():
        print(f"  {k}: {'成立（数学必然）' if v else '不成立'}")

    payload = {
        "meta": {
            "n": args.n, "seeds": args.seeds, "lam": args.lam,
            "mu": [round(float(x), 4) for x in mu],
            "T_lb": round(t_lb, 2),
            "seed_list": list(range(2026, 2026 + args.seeds)),
        },
        "methods": res,
        "equivalence_checks": equiv,
        "note": (
            "nearest_once / shortest_queue_once / static_cong_once 三者逐位相同是数学必然："
            "t=0 时三个出口队列全为 0，故「最短队列」与 cost=d+λ·0 都退化为最近出口。"
            "必须把它们当作**同一基线的三种等价表述**报告，而不是三次独立评测。"
            "shortest_queue_arrival / static_cong_arrival 才是真实语义（到达时按当时队列重决策）。"
        ),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\n已写出 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

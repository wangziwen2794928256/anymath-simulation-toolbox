#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_paper_numbers —— 从实验产物生成论文数值的唯一来源

为什么需要它
------------
``paper.tex`` 里的数字**系统性地过期**了：它们来自 ``eval_methods_fixed.py``
修正之前的那一版代码。逐个核对后发现，这不是"个别笔误"，而是整表偏位：

| 论文写的 | 实验产物里的真值 |
|---|---|
| 随机均衡 ``223.2±13.9``，Gini ``0.011`` | ``223.2±15.6``，Gini ``0.0333`` |
| 最近出口 ``426.7±5.3`` | ``426.7±6.0`` |
| 动态拥塞感知 ``204.1±25.7`` | ``184.5±15.9``（λ=3） |
| "λ 扫描单峰，λ=5 最优 177.9" | 真最小值在 **λ=3（184.5）**，λ=8 是 186.7，**不是单峰** |
| 消融"每 40/10/1 步：372.5 / 224.7 / 204.1" | 真实键是 **25/50/75/100% 个体动态：323.6 / 214.0 / 185.9 / 184.5** |

两张最危险的后果：

1. **``204.1`` 被当成了主结果**，但它其实属于消融里"每 1 步重决策"的那一行；
   主对比表里的动态策略是 ``184.5``。**两个不同实验的数字被混用了。**
2. **"λ=5 最优、单峰"这个结论不成立。** 真数据是 λ∈[0.5, 8] 都在 185–217 之间
   一个**很平**的区间，浅最小值在 λ=3。写成"单峰最优 λ=5"是把平坦读成了峰——
   而审稿人只要扫一眼扫描表就能发现。

这类错误的根因是**手抄数字**。所以本脚本把"论文里的数"变成
**由实验产物生成的派生物**：改了实验就重跑本脚本，论文数值不会自己漂。
``csf_gate.py`` 的数值冻结检查（正文数字必须能在 ``results/*.json`` 里找到来源）
正是为了守住这条链。

用法
----
    python make_paper_numbers.py            # 写出 results/paper_numbers.json
    python make_paper_numbers.py --check    # 只校验，不写（供门禁用）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
# 两个产物不在同一层：修正后的方法对比在 code/ 下，扫描结果在 code/results/ 下。
# 写死路径容易失效，所以两个位置都查一遍。
METHODS_CANDIDATES = (HERE / "evac_methods_fixed.json", RESULTS / "evac_methods_fixed.json")
SWEEPS_CANDIDATES = (RESULTS / "sweeps.json", HERE / "sweeps.json")


def _first_existing(cands: tuple[Path, ...], what: str) -> Path:
    for p in cands:
        if p.exists():
            return p
    raise SystemExit(f"找不到{what}，已查找：{[str(c) for c in cands]}")


def load(name: str) -> dict:
    if name == "evac_methods_fixed.json":
        p = _first_existing(METHODS_CANDIDATES, "方法对比结果")
    elif name == "sweeps.json":
        p = _first_existing(SWEEPS_CANDIDATES, "扫描结果")
    else:
        p = RESULTS / name
    return json.loads(p.read_text(encoding="utf-8"))


def build() -> dict:
    methods = load("evac_methods_fixed.json")
    sweeps = load("sweeps.json")

    m = methods["methods"]
    meta = methods["meta"]
    nea, rnd, dyn = m["nearest_once"], m["random_once"], m["dynamic_cong"]

    lam = {float(k): v for k, v in sweeps["lambda_sweep"].items()}
    lam_best = min(lam.items(), key=lambda kv: kv[1]["T_mean"])
    freq = sweeps["freq_ablation"]

    # λ 扫描是否真的是"单峰"？用数据回答，不要用印象回答。
    # 判据：存在一个内部极小值，且两侧都单调上升。
    ks = sorted(lam)
    ts = [lam[k]["T_mean"] for k in ks]
    i = ts.index(min(ts))
    left_rising = all(ts[j] > ts[j + 1] for j in range(i))
    right_rising = all(ts[j] < ts[j + 1] for j in range(i, len(ts) - 1))
    unimodal = left_rising and right_rising
    # 相对最优的容差带：与最优差 3% 以内的 λ 都算"平台"
    plateau = [k for k in ks if ts[ks.index(k)] <= ts[i] * 1.03]

    out = {
        "_source": {
            "methods": "results/evac_methods_fixed.json",
            "sweeps": "results/sweeps.json",
            "generated_by": "make_paper_numbers.py",
            "_note": "论文正文/表格里的每个数字都应能在本文件里找到；"
                     "改实验后重跑本脚本，不要手抄。",
        },
        "setup": {
            "N": meta["n"],
            "seeds": meta["seeds"],
            "T_lb_s": meta["T_lb"],
            "mu_per_s": meta["mu"],
            "lambda_main": meta["lam"],
        },
        # 主对比表：三个静态规则**逐位相同是数学必然**（t=0 时队列全为 0），
        # 所以只作为**一条基线**报告，并同时给出 reassign_count 以揭示真正的差异来源。
        "main": {
            "random_once": {
                "T": rnd["T_mean"], "T_std": rnd["T_std"], "gini": rnd["gini_mean"],
                "thr": rnd["thr_mean"], "flow": rnd["flow_mean"],
                "ratio_lb": rnd["ratio_vs_lb"], "reassign": rnd["reassign_count_mean"],
            },
            "static_rules_once": {
                "T": nea["T_mean"], "T_std": nea["T_std"], "gini": nea["gini_mean"],
                "thr": nea["thr_mean"], "flow": nea["flow_mean"],
                "ratio_lb": nea["ratio_vs_lb"], "reassign": nea["reassign_count_mean"],
                "equivalent": ["nearest_once", "shortest_queue_once", "static_cong_once"],
                "equivalence_verified": methods.get("equivalence_checks", {}),
            },
            "static_rules_on_arrival": {
                "T": m["shortest_queue_arrival"]["T_mean"],
                "T_std": m["shortest_queue_arrival"]["T_std"],
                "gini": m["shortest_queue_arrival"]["gini_mean"],
                "flow": m["shortest_queue_arrival"]["flow_mean"],
                "reassign": m["shortest_queue_arrival"]["reassign_count_mean"],
            },
            "dynamic_cong": {
                "T": dyn["T_mean"], "T_std": dyn["T_std"], "gini": dyn["gini_mean"],
                "thr": dyn["thr_mean"], "flow": dyn["flow_mean"],
                "ratio_lb": dyn["ratio_vs_lb"], "reassign": dyn["reassign_count_mean"],
            },
        },
        "lambda_sweep": {
            "table": {str(k): round(lam[k]["T_mean"], 1) for k in ks},
            "std": {str(k): round(lam[k]["T_std"], 1) for k in ks},
            "best_lambda": lam_best[0],
            "best_T": round(lam_best[1]["T_mean"], 1),
            # 由数据判定，而非由论文作者印象宣称
            "is_unimodal": unimodal,
            "plateau_within_3pct": plateau,
            "plateau_range": [min(plateau), max(plateau)] if plateau else None,
        },
        "freq_ablation": {
            k: {"T": v["T_mean"], "T_std": v["T_std"], "gini": v["gini_mean"],
                "flow": v["flow_mean"]}
            for k, v in freq.items()
        },
        "scale_sweep": {
            k: {"ours_T": v["ours"]["T_mean"], "nearest_T": v["nearest"]["T_mean"]}
            for k, v in sweeps["scale_sweep"].items()
        },
        "speed_sweep": {
            k: {"T": v["T_mean"], "T_std": v["T_std"]}
            for k, v in sweeps["speed_sweep"].items()
        },
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="生成论文数值的唯一来源")
    ap.add_argument("--check", action="store_true", help="只校验能否生成，不写文件")
    ap.add_argument("--out", default=str(RESULTS / "paper_numbers.json"))
    args = ap.parse_args()

    data = build()

    # 自检：把几个"曾经写错的结论"变成可执行断言，防止再次漂移
    problems: list[str] = []
    lam = data["lambda_sweep"]
    if lam["best_lambda"] != 3.0:
        problems.append(
            f"λ 最优值变了：数据说是 {lam['best_lambda']}，"
            f"论文里写的是 5 —— 必须同步正文，不要只改表")
    if lam["is_unimodal"]:
        problems.append("λ 扫描现在真的是单峰了，正文结论可以改回来")
    ma = data["main"]
    if abs(ma["dynamic_cong"]["T"] - 204.1) < 1e-9:
        problems.append("主对比的动态策略又变回 204.1 —— 那是消融里每 1 步的值，"
                        "不是主对比的值，疑似把两个实验混用了")

    if args.check:
        for p in problems:
            print(f"[WARN] {p}")
        print("生成校验：通过" if not problems else f"生成校验：{len(problems)} 处需人工确认")
        return 0

    Path(args.out).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写出 {args.out}")
    print(f"  λ 最优        : {lam['best_lambda']}（T={lam['best_T']} s），"
          f"单峰={lam['is_unimodal']}，平台={lam['plateau_range']}")
    print(f"  主对比 动态    : {ma['dynamic_cong']['T']}±{ma['dynamic_cong']['T_std']} s")
    print(f"  主对比 静态规则: {ma['static_rules_once']['T']}±{ma['static_rules_once']['T_std']} s"
          f"（三种等价表述，reassign={ma['static_rules_once']['reassign']}）")
    for p in problems:
        print(f"[WARN] {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python 侧同结构汇总（供 csf_parity 与 Julia 侧对拍）。

为什么单独一个脚本：对拍要求两侧输出**同构 JSON**（同键名、同结构），
否则 csf_parity 无法逐项比较。本脚本只做"调用 solve → 汇总 → 落盘"，
不含算法逻辑。

用法：
    python py_suite.py            # 写出 results/py_results.json
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from solve import simulate  # noqa: E402

SEEDS = list(range(2026, 2031))
# 与 Julia 侧同名的三个策略（命名必须一致，否则对拍工具无法配对）
POLICIES = {"nearest": "nearest", "random": "random", "waterfill": "static_balance"}


def build_py_instance_jl_like(inst: dict, seed: int) -> dict:
    """把实例重排成 Julia 侧手写解析器**能可靠读取**的扁平结构。

    Julia 侧不依赖 JSON.jl（AnyMath 装包受限），用手写正则解析。
    因此这里把站点与需求点写成**固定字段顺序**的扁平 JSON，
    避免嵌套结构导致解析失败。这是"跨语言数据交换要迁就最弱解析器"的实例。
    """
    return {
        "stations": [
            {"name": s["name"], "x": s["x"], "y": s["y"],
             "workstations": s["workstations"], "mu_per_min": s["mu_per_min"]}
            for s in inst["stations"]
        ],
        "x": inst["elderly"]["x"],
        "y": inst["elderly"]["y"],
        "earliest_min": inst["elderly"]["earliest_min"],
        "latest_min": inst["elderly"]["latest_min"],
    }


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "seedloop"
    inst = json.load(open(os.path.join(_HERE, "data", "instance.json"), encoding="utf-8"))
    os.makedirs(os.path.join(_HERE, "results"), exist_ok=True)
    out: dict = {"meta": {"lang": "python"}, "policies": {}}

    if mode == "single":
        # 单实例模式：所有策略解**同一份**实例 → 用于跨语言同实例对拍
        flat = build_py_instance_jl_like(inst, 2026)
        p = os.path.join(_HERE, "results", "instance_flat.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(flat, fh, ensure_ascii=False, indent=2)
        out["meta"]["instance"] = "instance_flat.json"
        for jl_name, py_name in POLICIES.items():
            r = simulate(inst, py_name, lam=1.0, seed=2026)
            out["policies"][jl_name] = {
                "T_mean": round(r["T"], 2), "T_std": 0.0, "T_seeds": [round(r["T"], 2)],
                "on_time_mean": round(r["on_time_rate"], 4),
                "gini_mean": round(r["gini_load"], 4),
                "ratio_lb_mean": round(r["ratio_lb"], 3),
                "served": [int(x) for x in r["served"]],
            }
        p2 = os.path.join(_HERE, "results", "py_results_single.json")
        print(f"→ 扁平实例 {p}")
        print(f"→ 结果 {p2}")
        print(f"  提示：Julia 侧用 CSF_INSTANCE={p} 运行即可同实例对拍")
    else:
        out["meta"]["seeds"] = SEEDS
        for jl_name, py_name in POLICIES.items():
            rows = [simulate(inst, py_name, lam=1.0, seed=s) for s in SEEDS]
            T = np.array([r["T"] for r in rows])
            out["policies"][jl_name] = {
                "T_mean": round(float(T.mean()), 2),
                "T_std": round(float(T.std(ddof=1)) if len(T) > 1 else 0.0, 2),
                "T_seeds": [round(r["T"], 2) for r in rows],
                "on_time_mean": round(float(np.mean([r["on_time_rate"] for r in rows])), 4),
                "gini_mean": round(float(np.mean([r["gini_load"] for r in rows])), 4),
                "ratio_lb_mean": round(float(np.mean([r["ratio_lb"] for r in rows])), 3),
                "served": [int(x) for x in rows[0]["served"]],
            }
        p2 = os.path.join(_HERE, "results", "py_results.json")
        print(f"→ {p2}")

    with open(p2, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    for name, d in sorted(out["policies"].items(), key=lambda x: x[1]["T_mean"]):
        print(f"  {name:<10} T={d['T_mean']:>7.2f}  "
              f"T/T_lb={d['ratio_lb_mean']:<5.3f}  served={d['served']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

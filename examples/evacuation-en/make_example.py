#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_example —— 为开源仓库生成旗舰示例的图与表

设计意图
--------
开源仓库的示例必须是**真的**：数字来自真实实验产物（``paper_numbers.json``，
由 ``make_paper_numbers.py`` 从 ``evac_methods_fixed.json`` / ``sweeps.json`` 生成），
图与表由本脚本**从这些数字生成**，而不是手绘或截图。

这样做的两个好处：
  1. 示例不会过期——改了实验就重跑本脚本，图、表与正文数字一起更新；
  2. 它同时是这套图表 DSL 的**可运行文档**：读者看到的就是 API 的用法。

输出
----
    figures/fig2_main.{pdf,svg,png}   主结果复合组图（4 面板，英文）
    tables/tab_main.{tex,csv,png}     主对比表（三线表 + CSV，英文）
    figures/*.labels.json             每张图的文字台账（供手工重绘矢量图）

用法
----
    python make_example.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1] / "skills"
sys.path.insert(0, str(SKILLS / "csf-figure-forge" / "scripts"))

import csf_fig  # noqa: E402
import csf_archetypes as A  # noqa: E402

NUMBERS = json.loads((HERE / "data" / "paper_numbers.json").read_text(encoding="utf-8"))


def panels() -> None:
    lam_all = NUMBERS["lambda_sweep"]["table"]
    lam_std = NUMBERS["lambda_sweep"]["std"]
    # λ=0 是"退化为最近出口"的**理论端点**（命题 2），值 426.7 s 比平台高 2.3 倍。
    # 把它画进同一张图会把 185–217 s 的平台压成一条平线——而平台正是本面板要说的结论。
    # 所以从 λ≥0.5 起画，λ=0 在 claim 里说明（并给出数值），另加容量下界作参照线。
    lam_keys = [k for k in lam_all if float(k) > 0]
    lam_x = [float(k) for k in lam_keys]
    lam_y = [lam_all[k] for k in lam_keys]
    t_lb = NUMBERS["setup"]["T_lb_s"]

    freq = NUMBERS["freq_ablation"]
    freq_keys = ["仅 t=0（静态）", "25% 个体动态", "50% 个体动态",
                 "75% 个体动态", "100% 个体动态（本文）"]
    freq_labels = ["static\n(t=0 only)", "25%", "50%", "75%", "100%\n(ours)"]
    freq_y = [freq[k]["T"] for k in freq_keys]

    scale = NUMBERS["scale_sweep"]
    sc_x = [int(k) for k in sorted(scale, key=int)]
    sc_ours = [scale[str(n)]["ours_T"] for n in sc_x]
    sc_nearest = [scale[str(n)]["nearest_T"] for n in sc_x]

    m = NUMBERS["main"]
    bar_labels = ["random", "static\n(3 rules)", "dynamic\n(ours)"]
    bar_y = [m["random_once"]["T"], m["static_rules_once"]["T"], m["dynamic_cong"]["T"]]
    bar_e = [m["random_once"]["T_std"], m["static_rules_once"]["T_std"],
             m["dynamic_cong"]["T_std"]]

    p = [
        {
            "kind": "line",
            "claim": (r"$\lambda\in[0.5,8]$: plateau within 3% of the optimum"),
            "xlabel": r"congestion weight $\lambda$",
            "ylabel": "clearance time $T$ (s)",
            "series": [
                {"label": "ours", "role": "ours", "x": lam_x, "y": lam_y,
                 "yerr": [lam_std[k] for k in lam_keys], "marker": "o"},
                {"label": "capacity lower bound", "role": "reference", "style": "--",
                 "x": [min(lam_x), max(lam_x)], "y": [t_lb, t_lb]},
            ],
        },
        {
            "kind": "bar",
            "claim": "Re-decision frequency, not cost design, drives the gain",
            "xlabel": "share of agents re-deciding",
            "ylabel": "clearance time $T$ (s)",
            # bar 面板的分类标签来自**显式 xticks**，不是 series[].label。
            # 省略它就是第一版的缺陷：5 根柱子只显示一个刻度标签 "T"。
            "xticks": freq_labels,
            "series": [
                {"label": "T (s)", "role": "ours_alt", "x": freq_labels, "y": freq_y},
            ],
        },
        {
            "kind": "line",
            "claim": "The advantage grows with instance size",
            "xlabel": "number of agents $N$",
            "ylabel": "clearance time $T$ (s)",
            "series": [
                {"label": "nearest exit", "role": "baseline",
                 "x": sc_x, "y": sc_nearest, "style": "--", "marker": "s"},
                {"label": "ours", "role": "ours", "x": sc_x, "y": sc_ours,
                 "marker": "o"},
            ],
        },
        {
            "kind": "bar",
            "claim": "Dynamic allocation reaches 82.5% of the capacity bound",
            "xlabel": "policy",
            "ylabel": "clearance time $T$ (s)",
            "xticks": bar_labels,
            "series": [
                {"label": "T (s)", "role": "improve", "x": bar_labels, "y": bar_y,
                 "yerr": bar_e},
            ],
        },
    ]
    A.result_panels(
        p, outdir=str(HERE / "figures"), name="fig2_main", ncols=2,
        lang="en",
        narrative_role="mechanism + main result",
        takeaway=("Capacity-proportional re-decision closes the gap to the capacity lower "
                  "bound; the residual is travel, not allocation."),
    )


def table() -> None:
    m = NUMBERS["main"]
    rows = [
        {"method": "Random assignment",
         "T (s)": (m["random_once"]["T"], m["random_once"]["T_std"]),
         "Gini": m["random_once"]["gini"],
         "T/T_lb": m["random_once"]["ratio_lb"],
         "flow E1/E2/E3": "/".join(str(v) for v in m["random_once"]["flow"]),
         "re-decision": str(m["random_once"]["reassign"])},
        # 三种静态规则在 t=0 队列全为 0 时逐位等价，故按一条基线报告；
        # re-decision 列 0--3 才是它们之间真正的区别。
        {"method": "Static rules*",
         "T (s)": (m["static_rules_once"]["T"], m["static_rules_once"]["T_std"]),
         "Gini": m["static_rules_once"]["gini"],
         "T/T_lb": m["static_rules_once"]["ratio_lb"],
         "flow E1/E2/E3": "/".join(str(v) for v in m["static_rules_once"]["flow"]),
         "re-decision": "0-3"},
        {"method": "Dynamic (ours)*",
         "T (s)": (m["dynamic_cong"]["T"], m["dynamic_cong"]["T_std"]),
         "Gini": m["dynamic_cong"]["gini"],
         "T/T_lb": m["dynamic_cong"]["ratio_lb"],
         "flow E1/E2/E3": "/".join(str(v) for v in m["dynamic_cong"]["flow"]),
         "re-decision": str(m["dynamic_cong"]["reassign"])},
        {"method": "Capacity lower bound",
         "T (s)": NUMBERS["setup"]["T_lb_s"],
         "Gini": "N/A", "T/T_lb": 1.0, "flow E1/E2/E3": "N/A", "re-decision": "N/A"},
    ]
    A.comparison_table(
        rows,
        ["T (s)", "Gini", "T/T_lb", "flow E1/E2/E3", "re-decision"],
        outdir=str(HERE / "tables"), name="tab_main",
        caption_key="method", highlight="min", lang="en",
        narrative_role="main comparison",
        takeaway=("Static rules coincide bit-for-bit because every queue is empty at "
                  "t=0; only decision frequency separates the policies."),
    )


def main() -> int:
    csf_fig.use_style("nature", cjk=False, lang="en", font_size=8.0)
    panels()
    table()
    print("\n示例产物已生成：")
    for d in ("figures", "tables"):
        for f in sorted(os.listdir(HERE / d)):
            print(f"  {d}/{f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

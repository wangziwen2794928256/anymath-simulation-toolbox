#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自拟例题出图：用 csf-figure-forge 的原型库，检验"图表对叙事的互补"能力。

四张图各有**明确论证功能**（不是装饰）：
  fig1_layout    场景与错配（承担 claim C2 的机制证据）
  fig2_compare   策略对比主结果（承担 C4）
  fig3_tradeoff  T 与均衡度的非一致（承担 C5 的边界论证）
  fig4_robust    鲁棒性（承担 C6）
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL = os.path.abspath(os.path.join(_HERE, "..", "..", "skills", "csf-figure-forge"))
sys.path.insert(0, os.path.join(_SKILL, "scripts"))

import csf_archetypes as A  # noqa: E402
import csf_fig  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

FIG = os.path.join(_HERE, "figures")


def fig_layout(inst: dict) -> None:
    """场景图：站点位置 + 容量份额 vs 就近承接份额（机制证据）。"""
    csf_fig.use_style("nature", cjk=True, font_size=8.5)
    pal = csf_fig.SemanticPalette()
    st = inst["stations"]
    el = inst["elderly"]
    d = inst["derived"]

    fig, ax = plt.subplots(figsize=(A.W_1_5 * A.MM_TO_INCH, A.W_1_5 * 0.72 * A.MM_TO_INCH), dpi=300)
    ax.scatter(el["x"], el["y"], s=8, c=pal("ours_alt"), alpha=0.5,
               edgecolors="white", linewidths=0.25, zorder=2, label=f"需求点（$N={len(el['x'])}$）")
    shares = [d["nearest_station_share"][s["name"]] for s in st]
    caps = [s["capacity_share"] for s in st]
    # 站点星标
    for s in st:
        ax.plot(s["x"], s["y"], marker="*", ms=17, color=pal("ours"),
                markeredgecolor="white", markeredgewidth=0.7, zorder=5, clip_on=False)
    # 标签交给**自动避让**算法（手摆偏移连续三轮都失败：重叠→跑轴外→又重叠）
    worst = max(st, key=lambda s: d["misalignment"][s["name"]])
    ann_text = f"错配 +{d['misalignment'][worst['name']]:.1%}"
    A.place_labels(
        ax,
        anchors=[(s["x"], s["y"]) for s in st] + [(worst["x"], worst["y"])],
        texts=[f"{s['name']}\n容量{caps[i]:.1%}｜就近{shares[i]:.1%}"
               for i, s in enumerate(st)] + [ann_text],
        fontsize=7.2,
        data_points=np.stack([el["x"], el["y"]], axis=1),
        marker_color=pal("ours"),
    )
    # 标注最大错配（文字位置也由上面的 place_labels 统一避让，此处不再重复画箭头）
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.005), frameon=False)
    ax.set_xlabel("$x$ / km")
    ax.set_ylabel("$y$ / km")
    ax.set_xlim(-0.4, inst["meta"]["area_km"] + 0.4)
    ax.set_ylim(-0.4, inst["meta"]["area_km"] + 0.4)
    ax.set_aspect("equal")
    ax.grid(alpha=0.15, lw=0.5)
    A._export(fig, FIG, "fig1_layout")
    plt.close(fig)


def fig_compare(res: dict) -> None:
    """主结果：四策略 KPI 对比（复合图）。"""
    csf_fig.use_style("nature", cjk=True, font_size=8.0)
    pol = res["policies"]
    names = {"random": "随机分配", "nearest": "就近分配",
             "static_balance": "容量比例（本文）", "dynamic": "反应式追逐最短队列"}
    order = ["nearest", "dynamic", "random", "static_balance"]
    role = {"nearest": "baseline", "dynamic": "ablation",
            "random": "baseline_2", "static_balance": "ours"}
    T = [pol[p]["T_mean"] for p in order]
    Ts = [pol[p]["T_std"] for p in order]
    O = [pol[p]["on_time_mean"] * 100 for p in order]
    G = [pol[p]["gini_mean"] for p in order]
    R = [pol[p]["ratio_lb_mean"] for p in order]

    panels = [
        dict(kind="bar", claim="容量比例分配把总完成时间降到 157.0 分钟（就近需 483.9）",
             ylabel="总完成时间 $T$ / 分钟", xticks=[names[p] for p in order],
             series=[dict(label="$T$", role="ours", y=T, yerr=Ts)]),
        dict(kind="bar", claim="准时率同步从 44.5% 提升到 81.2%",
             ylabel="准时率 / %", xticks=[names[p] for p in order],
             series=[dict(label="准时率", role="improve", y=O)],
             ylim=(0, 100)),
        dict(kind="line", claim="反应式规则在结构上失效（$T/T_{lb}$ 反而最高）",
             xlabel="策略（左→右按 $T$ 降序）", ylabel="$T/T_{\\mathrm{lb}}$",
             series=[dict(label="$T/T_{lb}$", role="ours", x=np.arange(len(order)), y=R, marker="o")],
             xticks=None),
        dict(kind="bar", claim="均衡度与效率不一致：容量比例分配并非 Gini 最小",
             ylabel="负载 Gini", xticks=[names[p] for p in order],
             series=[dict(label="Gini", role="reference", y=G)]),
    ]
    A.result_panels(panels, outdir=FIG, name="fig2_compare", ncols=2, width_mm=A.W_DOUBLE)


def fig_tradeoff(res: dict) -> None:
    """λ 权衡：T 单调上升而 Gini 单调下降 → 两目标不一致（边界论证）。"""
    csf_fig.use_style("nature", cjk=True, font_size=8.0)
    lam = np.array([0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0])
    T = np.array([res["lambda_sweep"][str(x)]["T_mean"] for x in lam])
    G = np.array([res["lambda_sweep"][str(x)]["gini_mean"] for x in lam])

    fig, ax1 = plt.subplots(figsize=(A.W_1_5 * A.MM_TO_INCH, 62 * A.MM_TO_INCH), dpi=300)
    pal = csf_fig.SemanticPalette()
    ax1.plot(lam, T, "-o", color=pal("ours"), lw=1.6, ms=3.5, label="总完成时间 $T$")
    ax1.set_xlabel(r"名额柔化参数 $\lambda$")
    ax1.set_ylabel("总完成时间 $T$ / 分钟", color=pal("ours"))
    ax1.tick_params(axis="y", labelcolor=pal("ours"))
    ax2 = ax1.twinx()
    ax2.plot(lam, G, "--s", color=pal("reference"), lw=1.6, ms=3.5, label="负载 Gini")
    ax2.set_ylabel("负载 Gini", color=pal("reference"))
    ax2.tick_params(axis="y", labelcolor=pal("reference"))
    ax1.grid(alpha=0.15, lw=0.5)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left")
    ax1.set_title("$T$ 上升而 Gini 下降：两个目标不一致", fontsize=8)
    A._export(fig, FIG, "fig3_tradeoff")
    plt.close(fig)


def fig_robust(res: dict) -> None:
    """鲁棒性：降速与缺勤的影响。"""
    csf_fig.use_style("nature", cjk=True, font_size=8.0)
    rob = res["robustness"]
    labels = list(rob.keys())
    T = [rob[k]["T_mean"] for k in labels]
    O = [rob[k]["on_time_mean"] * 100 for k in labels]
    panels = [
        dict(kind="bar", claim="降速 20% 仅使 $T$ 增加 0.9%（瓶颈在装车不在行驶）",
             ylabel="总完成时间 $T$ / 分钟", xticks=labels,
             series=[dict(label="$T$", role="ours", y=T,
                          yerr=[rob[k]["T_std"] for k in labels])],
             ylim=(min(T) * 0.97, max(T) * 1.005)),
        dict(kind="bar", claim="配送队缺勤 20% 对结果无影响（该资源不是瓶颈）",
             ylabel="准时率 / %", xticks=labels,
             series=[dict(label="准时率", role="improve", y=O)], ylim=(0, 100)),
    ]
    A.result_panels(panels, outdir=FIG, name="fig4_robust", ncols=2, width_mm=A.W_DOUBLE)


def main() -> int:
    os.makedirs(FIG, exist_ok=True)
    inst = json.load(open(os.path.join(_HERE, "data", "instance.json"), encoding="utf-8"))
    res = json.load(open(os.path.join(_HERE, "results", "selftest_results.json"), encoding="utf-8"))
    fig_layout(inst)
    fig_compare(res)
    fig_tradeoff(res)
    fig_robust(res)
    print("\n输出：")
    for f in sorted(os.listdir(FIG)):
        print("  ", f, f"{os.path.getsize(os.path.join(FIG, f)):,} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

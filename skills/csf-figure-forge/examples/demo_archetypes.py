#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原型库冒烟测试：四个原型各出一张图，用于视觉验收与回归。

载题用"多智能体疏散"（A 赛道典型场景），但四个原型都是领域无关的——
换题只需换内容，不换布局代码。
"""

from __future__ import annotations

import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
# examples/ -> csf-figure-forge/ -> skills/ -> 仓库根
_SKILL = os.path.abspath(os.path.join(_HERE, ".."))
_REPO = os.path.abspath(os.path.join(_SKILL, "..", ".."))
sys.path.insert(0, os.path.join(_SKILL, "scripts"))
sys.path.insert(0, os.path.join(_REPO, "skills", "csf-figure-forge", "scripts"))

import csf_archetypes as A  # noqa: E402
import csf_fig  # noqa: E402

OUT = os.path.join(_HERE, "out")


def demo_method_figure() -> None:
    """Figure 1：方法总览图（四层，自上而下 + 虚线反馈闭环）。

    拓扑设计遵循顶会读图习惯"自上而下、自左向右"：
      * 数据流只走**相邻层、同一次序**的垂直边；
      * 反馈用虚线且只跨一层（瓶颈色）；
      * 层内需要横向传递的量（如几何→容量）在同层内正向连接。
    `ArchSpec.check_topology()` 会自动检查这些约定，违反时打印警告。
    """
    csf_fig.use_style("nature", cjk=True, font_size=8.5)
    nodes = [
        # 第 0 层：环境
        A.ArchNode("site", "礼堂场地", "24 × 16 m\n三异宽出口", role="baseline", lane=0, order=0),
        A.ArchNode("cap", "出口容量模型", r"$\mu_e = w_e q$",
                   role="baseline", lane=0, order=1),
        # 第 1 层：智能体
        A.ArchNode("pop", "智能体种群", "N = 400\n位置 + 速度", role="ours_alt", lane=1, order=0),
        A.ArchNode("obs", "全局观测", r"$o_i=(p_i,\{Q_e\})$", role="ours_alt", lane=1, order=1),
        A.ArchNode("pol", "共享策略", r"$\pi_\theta(a_i\,|\,o_i)$", role="ours_alt", lane=1, order=2),
        # 第 2 层：算法
        A.ArchNode("cost", "边际代价", r"$c_i(e)=d_i(e)+\lambda Q_e$", role="ours", lane=2, order=0),
        A.ArchNode("assign", "出口分配", r"$a_i=\arg\min_e c_i(e)$", role="ours", lane=2, order=1),
        A.ArchNode("svc", "FIFO 服务", r"$\mu_e\Delta t$ 分数容量", role="ours", lane=2, order=2),
        # 第 3 层：评估与反馈
        A.ArchNode("kpi", "宏观指标", "T、Gini、瓶颈利用率", role="improve", lane=3, order=0),
        A.ArchNode("fb", "全局反馈", r"$Q_e(t)$ 回传", role="bottleneck", lane=3, order=1),
    ]
    edges = [
        # 同层横向（正向）
        ("site", "cap", "净宽", "solid"),
        ("pop", "obs", "状态", "solid"),
        ("obs", "pol", "观测", "solid"),
        ("cost", "assign", "代价", "solid"),
        ("assign", "svc", "指派", "solid"),
        ("kpi", "fb", "指标", "solid"),
        # 层间垂直（相邻层、同位次）
        ("cap", "obs", "服务率", "solid"),
        ("pol", "cost", "策略", "solid"),
        ("svc", "kpi", "离场事件", "solid"),
        # 反馈闭环（虚线、瓶颈色、跨一层）
        ("svc", "fb", "队列长度", "dashed"),
        ("fb", "cost", "拥塞回传", "dashed"),
    ]
    A.method_figure(
        lanes=["环境层 Environment", "智能体层 Agent", "算法层 Algorithm", "评估与反馈"],
        nodes=nodes, edges=edges, outdir=OUT, name="proto1_method", width_mm=A.W_DOUBLE,
    )


def demo_result_panels() -> None:
    """主结果复合组图 a/b/c/d。"""
    csf_fig.use_style("nature", cjk=True, font_size=8.0)
    rng = np.random.default_rng(0)
    lam = np.array([0, 0.5, 1, 2, 3, 5, 8, 13], dtype=float)
    T = np.array([426.7, 217.1, 209.2, 197.5, 184.5, 194.8, 186.7, 251.2])
    Ts = np.array([6.0, 3.9, 11.0, 13.4, 15.9, 20.1, 19.4, 57.9])

    panels = [
        dict(kind="bar", claim="均衡分配比就近分配快 47.7%",
             ylabel="总疏散时间 T / s", xticks=["随机", "最近出口", "静态类", "本文"],
             series=[dict(label="T", role="ours",
                          y=[223.2, 426.7, 426.7, 184.5],
                          yerr=[15.6, 6.0, 6.0, 15.9])]),
        dict(kind="line", claim="T(λ) 呈单峰，λ=3 最优",
             xlabel=r"拥塞权重 $\lambda$", ylabel="总疏散时间 T / s",
             series=[dict(label="本文策略", role="ours", x=lam, y=T, yerr=Ts, marker="o")],
             annotate=[dict(x=3.0, y=184.5, text="λ*=3", ha="center", va="bottom")]),
        dict(kind="line", claim="决策频率是主导因素（静态类首步退化）",
             xlabel="动态个体比例 α", ylabel="T / s",
             series=[dict(label="本文策略", role="ours", x=[0, .25, .5, .75, 1.0],
                          y=[426.7, 323.6, 214.0, 185.9, 184.5], marker="s"),
                     dict(label="静态类基线", role="baseline", x=[0, .25, .5, .75, 1.0],
                          y=[426.7, 426.7, 426.7, 426.7, 426.7], style="--")]),
        dict(kind="heatmap", claim="出口宽度差异越大，均衡收益越大",
             matrix=np.array([[56.8, 49.8, 46.6, 42.3],
                              [426.7, 341.3, 294.2, 284.4],
                              [184.5, 171.3, 157.1, 164.1]]),
             xticks=["原始", "收缩50%", "收缩90%", "相等"],
             yticks=["优势%", "最近出口", "本文"],
             colorbar_label="数值", cmap="viridis"),
    ]
    A.result_panels(panels, outdir=OUT, name="proto2_panels", ncols=2, width_mm=A.W_DOUBLE)


def demo_comparison_table() -> None:
    """主实验大表。"""
    rows = [
        dict(方法="随机出口", T=(223.2, 15.6), Thr=1.79, G=0.033, ratio=1.47),
        dict(方法="最近出口", T=(426.7, 6.0), Thr=0.94, G=0.322, ratio=2.80),
        dict(方法="最短队列（静态）", T=(426.7, 6.0), Thr=0.94, G=0.322, ratio=2.80, sig="†"),
        dict(方法="静态拥塞感知", T=(426.7, 6.0), Thr=0.94, G=0.322, ratio=2.80, sig="†"),
        dict(方法="IQL（独立学习）", T="N/A", Thr="N/A", G="N/A", ratio="N/A"),
        dict(方法="动态拥塞感知（本文）", T=(184.5, 15.9), Thr=2.17, G=0.083, ratio=1.21),
    ]
    A.comparison_table(
        # 注意：表头不要用 U+207B（上标减号）这类字符——微软雅黑无此字形，
        # csf_fig 的 strict_glyphs 会直接报错（这正是它该做的事）。
        # 上标一律走数学模式 $...$，由 mathtext 渲染。
        rows, ["T / s", r"Thr /(人$\cdot$s$^{-1}$)", "Gini", r"$T/T_{\mathrm{lb}}$"],
        outdir=OUT, name="proto3_table", caption_key="方法",
    )


def demo_ablation_matrix() -> None:
    """消融矩阵：组件轴 × 环境轴。"""
    M = np.array([
        [184.5, 186.8, 201.3, 214.6],   # 完整方法
        [197.5, 199.1, 213.4, 228.9],   # − 动态重分配（改为每 10 步）
        [224.3, 226.0, 241.2, 259.5],   # − 拥塞项（λ=0 近似）
        [312.7, 318.4, 336.1, 358.2],   # − 全局反馈（局部观测）
    ])
    A.ablation_matrix(
        M,
        row_labels=["完整方法", "−动态重分配", "−拥塞代价项", "−全局反馈"],
        col_labels=["标称", "速度异质", "出口缩窄10%", "N=500"],
        outdir=OUT, name="proto4_ablation", metric="T / s", lower_is_better=True,
    )


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    print("=== 原型 1：方法总览图 ===")
    demo_method_figure()
    print("=== 原型 2：主结果复合组图 ===")
    demo_result_panels()
    print("=== 原型 3：主实验大表 ===")
    demo_comparison_table()
    print("=== 原型 4：消融矩阵 ===")
    demo_ablation_matrix()
    print(f"\n全部输出在 {OUT}")
    for f in sorted(os.listdir(OUT)):
        print("  ", f, f"{os.path.getsize(os.path.join(OUT, f)):,} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

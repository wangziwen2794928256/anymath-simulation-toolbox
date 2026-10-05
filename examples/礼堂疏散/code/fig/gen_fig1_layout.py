#!/usr/bin/env python3
"""礼堂疏散 · 图 1 场景图（重做版）

对照 ``examples/礼堂疏散/figures/图1_礼堂平面.png`` 的四个具体缺陷逐条修：
  1. 图例文字"人员"压在 y=16 的边框线上
     → 图例移出绘图区（bbox_to_anchor 放到 axes 上方），不再压线
  2. ``E1 1.6m`` / ``E2 1.2m`` 文字叠在红色星标上、被边框裁掉
     → 出口标签改为**自动选边**：沿外法向放在墙外侧，星标完整可见
  3. 一个数据点画在 (0.3, 16.0) 边界之外
     → 位置生成改为带 **1 人半径的边界内缩**，并断言全部点落在场地内
  4. 图内字号/线宽不统一、无面板语境
     → 统一走 csf_fig 底座（SciencePlots + 中文字体接管）

用法：
    python gen_fig1_layout.py                 # 用论文默认种子 2026
    python gen_fig1_layout.py --seed 2026 --out ../figures-fixed
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
# 示例根目录：code/fig/ → code/ → 礼堂疏散/
_EXAMPLE = os.path.abspath(os.path.join(_HERE, "..", ".."))
_REPO = os.path.abspath(os.path.join(_EXAMPLE, "..", ".."))
sys.path.insert(0, os.path.join(_REPO, "skills", "csf-figure-forge", "scripts"))
import csf_fig  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

# --- 与 paper.tex 附录 A 完全一致的场地参数 ------------------------------- #
W, H = 24.0, 16.0
# 出口：(x, y, 宽度 m, 墙所在边)，E1 左墙 / E2 右墙 / E3 下墙
EXITS = [
    {"name": "E1", "x": 0.0, "y": 8.0, "w": 1.6, "side": "left"},
    {"name": "E2", "x": 24.0, "y": 8.0, "w": 1.2, "side": "right"},
    {"name": "E3", "x": 12.0, "y": 0.0, "w": 0.8, "side": "bottom"},
]
# 初始分布：60% 近 E3、25% 近 E2、15% 近 E1（刻意制造最近出口失衡）
CLUSTERS = [(12.0, 3.0, 0.60, 2.2, 1.6), (19.0, 8.0, 0.25, 2.2, 1.6), (5.0, 8.0, 0.15, 2.2, 1.6)]
PERSON_RADIUS = 0.30  # 修缺陷 3：边界内缩量（约一个行人半径）


def make_positions(seed: int, n: int = 400) -> np.ndarray:
    """与附录 make_positions 同分布，但保证所有点严格落在场地内。"""
    rng = np.random.default_rng(seed)
    parts = []
    for cx, cy, frac, sx, sy in CLUSTERS:
        m = int(round(n * frac))
        p = rng.normal(loc=(cx, cy), scale=(sx, sy), size=(m, 2))
        # 修缺陷 3：内缩一个行人半径，杜绝点画到墙外/墙线上
        p[:, 0] = np.clip(p[:, 0], PERSON_RADIUS, W - PERSON_RADIUS)
        p[:, 1] = np.clip(p[:, 1], PERSON_RADIUS, H - PERSON_RADIUS)
        parts.append(p)
    pos = np.concatenate(parts)[:n].copy()
    assert pos.shape == (n, 2), pos.shape
    assert (pos[:, 0] >= PERSON_RADIUS).all() and (pos[:, 0] <= W - PERSON_RADIUS).all()
    assert (pos[:, 1] >= PERSON_RADIUS).all() and (pos[:, 1] <= H - PERSON_RADIUS).all()
    return pos


def _label_anchor(ex: dict) -> tuple[float, float, str, str]:
    """出口标签一律放在**房间内侧**，沿墙内法向偏移。

    这是迭代中实测出的结论：放到墙外会同时踩两个坑——
      * 左墙外会与 y 轴刻度文字（如 "7.5"）重叠（视觉验收 ①）；
      * 左/右墙外会与场地边框、坐标轴区域互相挤压。
    内侧放置后星标完整可见，且不与任何轴元素相交。

    返回 (文字 x, 文字 y, 水平对齐, 垂直对齐)，坐标为数据坐标。
    """
    pad = 0.55  # 距星标中心的室内偏移（m）
    if ex["side"] == "left":
        return ex["x"] + pad, ex["y"], "left", "center"
    if ex["side"] == "right":
        return ex["x"] - pad, ex["y"], "right", "center"
    # 下墙 E3：星标处正好是人群密集区，标签若居中上移会压住点云
    # （视觉验收 ③）。右下角室内为空白区；y 取 1.45 而非 1.05，是为让
    # 第二行「0.8 m」与 y=0 的场地底边框留出间距（视觉验收 ④）。
    return 23.5, 1.45, "right", "center"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--out", default=os.path.join(_EXAMPLE, "figures-fixed"))
    args = ap.parse_args()

    csf_fig.use_style("nature", cjk=True, font_size=9.0, strict_glyphs=True)
    pal = csf_fig.SemanticPalette()

    pos = make_positions(args.seed, args.n)

    fig, ax = plt.subplots(figsize=(120 / 25.4, 120 / 25.4 * 0.72), dpi=300)
    ax.set_xlim(-2.6, W + 2.6)  # 给左右墙外的出口标签留位置
    ax.set_ylim(-2.6, H + 1.4)
    ax.set_aspect("equal")

    # 场地边框（加粗、无填充）
    ax.add_patch(
        plt.Rectangle((0, 0), W, H, fill=False, lw=1.6, edgecolor="#4D4D4D", zorder=2)
    )

    # 人群（低饱和蓝，不抢出口的视觉权重）
    ax.scatter(
        pos[:, 0], pos[:, 1], s=11, c=pal("ours_alt"), alpha=0.62,
        edgecolors="white", linewidths=0.35, zorder=3, label=f"人员（$N={args.n}$）",
    )

    # 出口：星标 + 自动选边标签（修缺陷 2）
    for ex in EXITS:
        ax.plot(
            ex["x"], ex["y"], marker="*", ms=17, color=pal("bottleneck"),
            markeredgecolor="white", markeredgewidth=0.7, zorder=5, clip_on=False,
        )
        tx, ty, ha, va = _label_anchor(ex)
        # 出口标签：第一行编号，第二行宽度（两行避免长文本横向溢出）
        ax.text(
            tx, ty, f"{ex['name']}\n{ex['w']} m", ha=ha, va=va, fontsize=9,
            linespacing=1.45, color=pal("bottleneck"), zorder=6, clip_on=False,
        )

    # 修缺陷 1：图例移到绘图区之外，不压边框、不压数据
    ax.legend(
        loc="lower center", bbox_to_anchor=(0.5, 1.005), ncol=1,
        frameon=False, handletextpad=0.4, borderaxespad=0.0,
    )

    ax.set_xlabel("$x$ / m")
    ax.set_ylabel("$y$ / m")
    ax.set_title("礼堂平面与 400 名智能体初始分布（60% 近 E3）", fontweight="bold", pad=16)

    # 出口容量比标注：把"三异宽出口"这个关键设定显式写出来。
    # 位置经视觉验收调整：放在**右上角室内空白区**，避开下墙的 E3 星标与标签
    # （初版放过右下角，结果盖住了 E3 出口星标——视觉验收 ②）。
    ax.text(
        0.975, 0.935,
        r"服务率 $\mu_e=w_e q$,  $q=0.73$ 人/(m$\cdot$s)" + "\n"
        r"$\mu_1{:}\mu_2{:}\mu_3=1.168{:}0.876{:}0.584$ 人/s",
        transform=ax.transAxes, ha="right", va="top", fontsize=8,
        linespacing=1.5,
        bbox=dict(boxstyle="round,pad=0.42", fc="white", ec="#CFCECE", lw=0.7, alpha=0.95),
        zorder=7,
    )

    written = csf_fig.FigSpec.__new__(csf_fig.FigSpec)  # 仅复用导出逻辑
    written.fig = fig
    written.dpi = 300
    written.boxes = []
    written.canvas = (W, H)
    written.palette = pal
    paths = csf_fig.FigSpec.finalize(
        written, os.path.abspath(args.out), "图1_礼堂平面_重做版"
    )
    print("seed =", args.seed, "| 点数 =", len(pos),
          "| x∈[%.2f,%.2f] y∈[%.2f,%.2f]" % (pos[:, 0].min(), pos[:, 0].max(), pos[:, 1].min(), pos[:, 1].max()))
    for fmt, p in paths.items():
        print(f"  {fmt}: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

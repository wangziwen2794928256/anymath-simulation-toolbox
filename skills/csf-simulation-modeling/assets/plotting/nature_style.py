# 已停用（2026-10-03）：绘图与论文框架统一改用 math-modeling-contest skill（其 references/nature-figure-guide.md + scripts/plot_figures_nature.py）。
# 本文件保留备用，暂不用于正式出图。
"""Nature / 顶刊顶会风格的 matplotlib 通用配置与绘图工具。

用法：
    import sys; sys.path.insert(0, "assets/plotting")
    from nature_style import apply_nature_style, NATURE
    apply_nature_style(cjk=True)   # 全局生效（中文标题需要）
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.plot(x, y, color=NATURE["proposed"], lw=2)
    save_figure(fig, "out/fig1", dpi=300)
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 色盲安全 8 色（Okabe-Ito，Wong Nature Methods 2011）
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
             "#0072B2", "#D55E00", "#CC79A7", "#000000"]

# 语义配色（Nature 风：一眼看出“谁好谁坏”）
NATURE = {
    "proposed": "#0F4D92",   # 主方法 / 最优解（深蓝，主角）
    "baseline": "#7F7F7F",   # 基线 / 对照（中性灰，配角）
    "critical": "#D62728",   # 瓶颈 / 风险 / 关键（红）
    "accent1":  "#E69F00",   # 次优 / 辅助（橙）
    "accent2":  "#009E73",   # 次优 / 辅助（绿）
    "fill":     "#A6C8E8",   # 淡蓝填充
    "grey":     "#B0B0B0",
    "dark":     "#222222",
}

_CMAP_SAFE = "viridis"


def _register_cjk():
    candidates = ["PingFang SC", "Heiti SC", "Songti SC", "STHeiti",
                  "SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
    for name in candidates:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
        except Exception:
            continue
        try:
            font_manager.fontManager.addfont(path)
            font_manager.findfont(name)
            return name
        except Exception:
            continue
    return None


def apply_nature_style(cjk: bool = False):
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.7,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": False,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
        "axes.prop_cycle": mpl.cycler(color=OKABE_ITO),
        "legend.frameon": False,
        "legend.borderpad": 0.4,
    })
    cjk_name = None
    if cjk:
        cjk_name = _register_cjk()
        if cjk_name:
            mpl.rcParams["font.family"] = "sans-serif"
            mpl.rcParams["font.sans-serif"] = [cjk_name, "Helvetica", "Arial"]
            mpl.rcParams["axes.unicode_minus"] = False
    return cjk_name


def style_axes(ax, grid: bool = False, ylabel: str = "", xlabel: str = "",
               title: str = "", legend: bool = False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(True, linestyle="--", alpha=0.3, linewidth=0.5)
        ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, loc="left", fontweight="bold")
    if legend:
        ax.legend()
    return ax


def save_figure(fig, path: str, dpi: int = 300, formats=("pdf", "png")):
    for fmt in formats:
        fig.savefig(f"{path}.{fmt}", dpi=dpi, bbox_inches="tight", pad_inches=0.02)


def bar_with_error(ax, labels, means, stds, *, highlight=-1,
                   ylabel="", title="", xlabel="", value_fmt=".3g"):
    colors = [NATURE["proposed"] if i == highlight else NATURE["baseline"]
              for i in range(len(means))]
    bars = ax.bar(labels, means, yerr=stds, capsize=3, color=colors,
                  edgecolor="white", linewidth=0.6, error_kw={"lw": 0.8})
    for b, m, sd in zip(bars, means, stds):
        ax.text(b.get_x() + b.get_width() / 2, m + sd * 0.6, f"{m:{value_fmt}}",
                ha="center", va="bottom", fontsize=7.5)
    style_axes(ax, ylabel=ylabel, xlabel=xlabel, title=title)
    return bars


def line_with_ci(ax, x, mean, ci, *, color=NATURE["proposed"], label="",
                 xlabel="", ylabel="", title=""):
    ax.plot(x, mean, color=color, lw=1.8, label=label)
    ax.fill_between(x, mean - ci, mean + ci, color=color, alpha=0.18, linewidth=0)
    style_axes(ax, ylabel=ylabel, xlabel=xlabel, title=title)
    if label:
        ax.legend()
    return ax


def annotate_significance(ax, x1, x2, y, pvalue, h=None, text=None):
    if h is None:
        ylim = ax.get_ylim()
        h = 0.03 * (ylim[1] - ylim[0])
    else:
        pass
    if pvalue < 0.001:
        stars = "***"
    elif pvalue < 0.01:
        stars = "**"
    elif pvalue < 0.05:
        stars = "*"
    else:
        stars = "ns"
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=0.8, color=NATURE["dark"])
    ax.text((x1 + x2) / 2, y + h, text or stars, ha="center", va="bottom", fontsize=8)
    ax.set_ylim(ax.get_ylim()[0], y + 2.5 * h)
    return ax


def heatmap(ax, matrix, *, xlabels=None, ylabels=None, cmap=_CMAP_SAFE,
            cbar_label="", title="", annotate=False):
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, interpolation="nearest")
    if xlabels is not None:
        ax.set_xticks(range(len(xlabels)), labels=xlabels, rotation=45, ha="right")
    if ylabels is not None:
        ax.set_yticks(range(len(ylabels)), labels=ylabels)
    if annotate:
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center",
                        fontsize=6.5, color="white")
    cbar = ax.figure.colorbar(im, ax=ax, pad=0.02)
    cbar.ax.set_ylabel(cbar_label, fontsize=8)
    style_axes(ax, title=title)
    return ax


# ---- 常用画布尺寸（Nature 单/双栏，单位英寸）----
FIGSIZE_SINGLE = (3.5, 2.6)
FIGSIZE_1P5 = (4.6, 3.0)
FIGSIZE_DOUBLE = (7.0, 3.0)


def multi_panel(nrows, ncols, size=FIGSIZE_DOUBLE, **subplots_kw):
    """统一风格的多面板画布，返回 (fig, axes)。"""
    fig, axes = plt.subplots(nrows, ncols, figsize=size, **subplots_kw)
    return fig, axes


# ---- Method/框架图 与 复合组图 辅助 ----
def panel_label(ax, label, x=-0.10, y=1.05, size=9):
    """在面板左上角加 (a)/(b) 子图标签。"""
    ax.text(x, y, label, transform=ax.transAxes, fontsize=size,
            fontweight="bold", ha="right", va="bottom", color=NATURE["dark"])
    return ax


def draw_box(ax, xy, w, h, text, fc="#EEF3FA", ec=NATURE["proposed"],
             lw=1.2, rounded=True, fontsize=8, tc=NATURE["dark"]):
    """画一个流程框。xy 为左下角，w/h 为宽高。"""
    from matplotlib.patches import FancyBboxPatch
    box = FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
                         linewidth=lw, edgecolor=ec, facecolor=fc)
    ax.add_patch(box)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=tc)
    return box


def draw_arrow(ax, p0, p1, color=NATURE["grey"], lw=1.2, style="-|>",
               shrinkA=2, shrinkB=2):
    """画一条连接箭头。p0/p1 为 (x,y)。"""
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                shrinkA=shrinkA, shrinkB=shrinkB))
    return ax


# ===== 顶刊扩展调色板与工具（源自 figures4papers / engineering-figure-agent 蒸馏）=====
PUB_PALETTE = {
    "blue_main": "#0F4D92",       # 主方法 / 中心机制
    "blue_secondary": "#3775BA",  # 主方法变体
    "green_1": "#DDF3DE", "green_2": "#AADCA9", "green_3": "#8BCF8B",  # 改善/有利
    "red_1": "#F6CFCB", "red_2": "#E9A6A1", "red_strong": "#B64342",  # 基线/竞争/不利
    "neutral": "#CFCECE", "neutral_dark": "#4D4D4D",                   # 底衬/灰阶
    "highlight": "#FFD700",       # 唯一强调色，少用
    "teal": "#42949E", "violet": "#9A4D8E",
}
PUB_SERIES = ["#0F4D92", "#8BCF8B", "#B64342", "#42949E", "#9A4D8E", "#4D4D4D"]


def apply_publication_style(font_size=8, axes_linewidth=0.8, svg_editable=True):
    """顶刊风格全局设置（嵌入论文用 font_size=8~9，单独成图用 14~16）。"""
    mpl.rcParams.update({
        "font.size": font_size,
        "axes.linewidth": axes_linewidth,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
        "svg.fonttype": "none" if svg_editable else "path",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def finalize_figure(fig, path, dpi=300, formats=("pdf", "svg", "png"), pad=0.02):
    """投稿级导出：PDF 矢量 + SVG 可编辑 + PNG 300dpi，白底。"""
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        fig.savefig(f"{path}.{fmt}", dpi=dpi, bbox_inches="tight",
                    pad_inches=pad, facecolor="white")

# -*- coding: utf-8 -*-
"""Render a terminal-style demo figure of csf_gate.py real output (run on the Chinese test paper)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm

# fonts: CJK + mono
cjk_candidates = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]
mono_candidates = ["Consolas", "DejaVu Sans Mono"]
def pick(cands):
    installed = {f.name for f in fm.fontManager.ttflist}
    for c in cands:
        if c in installed:
            return c
    return None
CJK = pick(cjk_candidates) or "sans-serif"
MONO = pick(mono_candidates) or "monospace"

BG      = "#0d1117"   # terminal background
TITLEBG = "#161b22"
GREEN   = "#3fb950"
RED     = "#f85149"
YELLOW  = "#d29922"
DIM     = "#8b949e"
FG      = "#c9d1d9"
CYAN    = "#58a6ff"

W, H = 16, 9.4
fig = plt.figure(figsize=(W, 11.7), dpi=180)
fig.patch.set_facecolor(BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100); ax.set_ylim(26.5, 100); ax.axis("off")

# window frame
ax.add_patch(FancyBboxPatch((1.2, 26.5), 97.6, 71.3, boxstyle="round,pad=0,rounding_size=1.2",
                            fc=BG, ec="#30363d", lw=1.5))
# title bar
ax.add_patch(FancyBboxPatch((1.2, 90.4), 97.6, 8.4, boxstyle="round,pad=0,rounding_size=1.2",
                            fc=TITLEBG, ec="none"))
ax.add_patch(plt.Rectangle((1.2, 90.4), 97.6, 4.2, fc=TITLEBG, ec="none"))
# traffic lights
for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
    ax.add_patch(plt.Circle((4.2 + i * 2.6, 94.6), 0.95, fc=c, ec="none"))
ax.text(15, 94.6, "csf_gate.py  --tex examples/礼堂疏散/paper.tex  --lang zh",
        color=DIM, fontsize=12.5, family=[MONO, CJK], va="center")

def line(y, text, color=FG, size=12.5, x=4.0, weight="normal"):
    ax.text(x, y, text, color=color, fontsize=size, family=[MONO, CJK], va="top", weight=weight)

y = 87.5
line(y, "==========================================================================", DIM); y -= 3.4
line(y, "csf-gate · 门禁实测：中文测试靶稿（骨架稿，故意未达交付标准）", FG, 13, weight="bold"); y -= 3.2
line(y, "==========================================================================", DIM); y -= 3.6

line(y, "[ERROR] 8 项 —— 不通过不许进入下一阶段", RED, 13, weight="bold"); y -= 3.4
errors = [
    ("1", "SECTION_TOO_THIN",   "章节「引言」仅 16 行（下限 40）；「实验」仅 48 行（下限 100）"),
    ("2", "TOO_FEW_FIGURES",    "正文只有 3 个 figure，要求 ≥5（缺方法总览/主结果组图/消融）"),
    ("3", "TOO_FEW_TABLES",     "正文只有 2 个 table，要求 ≥4（缺符号表/参数表/消融表）"),
    ("4", "MAS_INCOMPLETE",     "多智能体形式化缺要素：奖励 R、信用分配、涌现/宏观量"),
]
for num, rule, desc in errors:
    ax.text(4.0, y, " × ", color=RED, fontsize=13, family=[MONO, CJK], va="top", weight="bold")
    ax.text(7.2, y, f"({rule})", color=CYAN, fontsize=12.5, family=[MONO, CJK], va="top", weight="bold")
    ax.text(7.2, y - 2.9, desc, color=FG, fontsize=12, family=[MONO, CJK], va="top")
    y -= 6.4

y -= 0.6
line(y, "[WARN] 4 项 —— 需人工确认", YELLOW, 13, weight="bold"); y -= 3.2
warns = [
    "NUMBER_REPEATED   数值 426.7 在正文出现 13 次 → 应绑定 results/*.json（frozen_numbers）",
    "UNCITED_BIBITEM   12 条参考文献未被 \\cite → 终稿门禁要求全部被引用",
]
for w in warns:
    ax.text(4.0, y, " ! ", color=YELLOW, fontsize=13, family=[MONO, CJK], va="top", weight="bold")
    ax.text(7.2, y, w, color=FG, fontsize=12, family=[MONO, CJK], va="top")
    y -= 3.4

y -= 1.2
ax.add_patch(plt.Rectangle((3.0, y - 3.6), 94, 6.2, fc="#2d1215", ec=RED, lw=1.2))
ax.text(50, y - 0.6, "结论：不通过 —— 8 个 ERROR，4 个 WARN（规范不再只是「劝阻」，而是会报错的门禁）",
        color=RED, fontsize=13.5, family=[MONO, CJK], ha="center", va="top", weight="bold")

plt.savefig(r"D:\anymath-and-simulation\docs\demo-gates-in-action.png",
            facecolor=BG, bbox_inches="tight", pad_inches=0.15)
print("saved")

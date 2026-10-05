# -*- coding: utf-8 -*-
"""按 math-modeling-contest 的规范出图：SimHei 优先 + Nature 语义配色 + 全中文标签。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# —— 完全照搬 math-modeling-contest 的字体与配色约定 ——
plt.rcParams['font.family'] = 'sans-serif'
from matplotlib import font_manager as _fm
for _n in ['SimHei','PingFang SC','Songti SC','Heiti SC']:
    try: _fm.fontManager.addfont(_fm.findfont(_n, fallback_to_default=False))
    except Exception: pass
plt.rcParams['font.sans-serif'] = ['SimHei','PingFang SC','Songti SC','Arial','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams.update({
    'axes.spines.right': False, 'axes.spines.top': False,
    'legend.frameon': False, 'axes.linewidth': 0.8,
    'figure.dpi': 300, 'savefig.dpi': 300, 'font.size': 9,
    'axes.titlesize': 11, 'axes.labelsize': 9, 'legend.fontsize': 8,
    'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.12,
})
PALETTE = {"blue_main":"#0F4D92","blue_secondary":"#3775BA","green_3":"#8BCF8B",
           "red_strong":"#B64342","neutral_light":"#CFCECE","neutral_mid":"#767676",
           "neutral_dark":"#4D4D4D","neutral_black":"#272727","teal":"#42949E","violet":"#9A4D8E"}
OUT = Path("演示/figures")

# 图1：复合组图（a 成料数对比，b 作业效率）——用外部 skill 的语义配色
done=[310,280,316]; ideal=[384,368,392]; eff=[80.73,76.09,80.61]
x=np.arange(3); w=0.36
fig, axes=plt.subplots(1,2, figsize=(7.2,2.8))
ax=axes[0]
ax.bar(x-w/2, ideal, w, label="理想上界", color=PALETTE["neutral_light"], edgecolor=PALETTE["neutral_dark"], linewidth=0.6)
ax.bar(x+w/2, done, w, label="本文策略", color=PALETTE["blue_main"], edgecolor="white", linewidth=0.5)
for xi,iv,dv in zip(x,ideal,done):
    ax.text(xi-w/2, iv+7, f"{iv}", ha="center", fontsize=8, color=PALETTE["neutral_dark"])
    ax.text(xi+w/2, dv+7, f"{dv}", ha="center", fontsize=8, color=PALETTE["blue_main"])
ax.set_ylim(0,430); ax.set_xticks(x); ax.set_xticklabels(["第1组","第2组","第3组"])
ax.set_xlabel("系统作业参数组"); ax.set_ylabel("8小时成料数 / 件")
ax.legend(loc="lower right")
ax.text(-0.12,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight="bold")
ax=axes[1]
ax.bar(["第1组","第2组","第3组"], eff, color=[PALETTE["blue_main"]]*3, edgecolor="white", linewidth=0.5)
for i,e in enumerate(eff):
    ax.text(i, e+1.5, f"{e}%", ha="center", fontsize=8, color=PALETTE["blue_main"])
ax.set_ylim(0,100); ax.axhline(100, color=PALETTE["neutral_mid"], ls="--", lw=0.8)
ax.set_xlabel("系统作业参数组"); ax.set_ylabel("作业效率 / %")
ax.text(-0.12,1.04,"b",transform=ax.transAxes,fontsize=11,fontweight="bold")
fig.tight_layout()
fig.savefig(OUT/"复合组图_成料数效率.png"); fig.savefig(OUT/"复合组图_成料数效率.pdf"); plt.close(fig)

# 图2：系统结构示意图（用外部 skill 的语义配色：设备=蓝、关键=红、底衬=灰）
fig, ax=plt.subplots(figsize=(7.2,2.6)); ax.set_xlim(0,14); ax.set_ylim(0,4.2); ax.axis("off")
ax.plot([1,13],[2.4,2.4], color=PALETTE["neutral_light"], lw=2)
for i in range(8):
    x=1.6+i*1.4
    ax.add_patch(plt.Rectangle((x-0.35,2.55),0.7,0.7, fc="#EEF3FA", ec=PALETTE["blue_main"], lw=1))
    ax.text(x,2.9,f"CNC{i+1}",ha="center",va="center",fontsize=7,color=PALETTE["neutral_black"])
    ax.plot([x,x],[2.4,2.55],color=PALETTE["neutral_mid"],lw=1)
ax.add_patch(plt.Rectangle((2.0,1.7),0.9,0.5, fc="#FBEAEA", ec=PALETTE["red_strong"], lw=1))
ax.text(2.45,1.95,"RGV",ha="center",va="center",fontsize=7.5,color=PALETTE["neutral_black"])
ax.annotate("",xy=(2.0,2.35),xytext=(2.45,2.2),arrowprops=dict(arrowstyle="-|>",color=PALETTE["red_strong"],lw=1))
ax.add_patch(plt.Rectangle((0.5,0.5),13,0.5, fc="#F2F2F2", ec=PALETTE["neutral_mid"], lw=0.8))
ax.text(7,0.75,"上料传送带 / 下料传送带",ha="center",va="center",fontsize=7,color=PALETTE["neutral_dark"])
fig.savefig(OUT/"系统结构示意图.png"); fig.savefig(OUT/"系统结构示意图.pdf"); plt.close(fig)
print("figures done")

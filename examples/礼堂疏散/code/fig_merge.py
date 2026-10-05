# -*- coding: utf-8 -*-
"""合并图4/5/6 为一张 2×2 复合图：(a)频率消融 (b)λ消融 (c)Q学习训练曲线 (d)Climbing IQL vs QMIX。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json
from matplotlib import font_manager as fm
for n in ['SimHei','PingFang SC','Songti SC','Heiti SC']:
    try: fm.fontManager.addfont(fm.findfont(n, fallback_to_default=False))
    except Exception: pass
plt.rcParams['font.family']='sans-serif'
plt.rcParams['font.sans-serif']=['SimHei','PingFang SC','Songti SC','Arial']
plt.rcParams['axes.unicode_minus']=False
plt.rcParams.update({'axes.spines.right':False,'axes.spines.top':False,'legend.frameon':False,
 'axes.linewidth':0.8,'figure.dpi':300,'savefig.dpi':300,'font.size':9,'axes.labelsize':8.5,
 'legend.fontsize':7,'figure.facecolor':'white','savefig.facecolor':'white','savefig.bbox':'tight'})
P={"navy":"#1F4E79","blue":"#2E75B6","blue2":"#6EA8D8","orange":"#E0863B","green":"#4E9A67",
   "red":"#C0564A","purple":"#7A5FA8","grey":"#9AA0A6","light":"#D8DDE1","dark":"#26282B"}
OUT="例题/礼堂疏散/figures"
D=json.load(open("/tmp/evac_ablation.json")); C=json.load(open("/tmp/climbing.json")); Q=json.load(open("/tmp/dqn_results.json"))
fig,axes=plt.subplots(2,2,figsize=(7.4,5.0))
# (a) 频率消融
ax=axes[0,0]; freq=list(D["freq"].keys()); vals=[D["freq"][k] for k in freq]
cols=[P["navy"] if v==min(vals) else P["blue2"] for v in vals]
b=ax.bar(freq,vals,color=cols,edgecolor='white',lw=0.5)
for bi,v in zip(b,vals): ax.text(bi.get_x()+bi.get_width()/2,v+8,f"{v:.0f}",ha='center',fontsize=7)
ax.set_ylim(0,470); ax.set_ylabel("总疏散时间/s"); ax.set_xlabel("重分配频率"); ax.set_xticklabels(freq,rotation=15,fontsize=7)
ax.text(-0.14,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (b) λ消融
ax=axes[0,1]; lams=[float(k) for k in D["lam"]]; tvals=[D["lam"][str(int(k))] for k in lams]
ax.plot(lams,tvals,'-o',color=P["blue"],lw=1.6,ms=4)
ax.axhline(177.9,color=P["green"],ls='--',lw=0.9,label="最优 λ=5")
ax.set_xlabel("拥塞权重 λ"); ax.set_ylabel("总疏散时间/s"); ax.legend(loc='upper right')
ax.text(-0.14,1.04,"b",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (c) Q学习训练曲线
ax=axes[1,0]; m=np.array(Q["curve_mean"]); s=np.array(Q["curve_std"]); ep=np.arange(len(m))
ax.plot(ep,m,color=P["blue"],lw=1.5); ax.fill_between(ep,m-s,m+s,color=P["blue"],alpha=0.15,lw=0)
ax.set_xlabel("训练回合"); ax.set_ylabel("回合奖励"); ax.set_title("线性 Q 学习",fontsize=8,loc='left')
ax.text(-0.14,1.04,"c",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (d) Climbing IQL vs QMIX
ax=axes[1,1]
for a in ["iql","qmix"]:
    c=np.array(C[a]["curve_mean"]); x=np.arange(len(c))*20
    ax.plot(x,c,color=P["red"] if a=="iql" else P["navy"],lw=1.5,label=a.upper())
ax.axhline(11,color=P["green"],ls='--',lw=0.9,label="最优 11"); ax.axhline(7,color=P["orange"],ls='--',lw=0.9,label="次优 7")
ax.set_xlabel("训练回合"); ax.set_ylabel("共同收益"); ax.set_title("Climbing Game",fontsize=8,loc='left'); ax.legend(loc='lower right',fontsize=7)
ax.text(-0.14,1.04,"d",transform=ax.transAxes,fontsize=11,fontweight='bold')
fig.suptitle("图 5  消融与学习式方法（a 频率消融；b λ 消融；c 训练曲线；d IQL vs QMIX）",x=0.08,ha='left',fontsize=9,fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.94])
fig.savefig(f"{OUT}/AI图5_消融与学习.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图5_消融与学习.pdf"); plt.close(fig)
print("merged fig done")

# -*- coding: utf-8 -*-
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
 'axes.linewidth':0.8,'figure.dpi':300,'savefig.dpi':300,'font.size':9,'axes.labelsize':9,
 'legend.fontsize':8,'figure.facecolor':'white','savefig.facecolor':'white','savefig.bbox':'tight'})
P={"blue":"#0F4D92","blue2":"#3775BA","green":"#8BCF8B","red":"#B64342","grey":"#CFCECE","dark":"#4D4D4D","black":"#272727"}
OUT="例题/礼堂疏散/figures"
res=json.load(open("/tmp/evac_extra.json"))

# 图7 Gini 均衡度对比
fig,ax=plt.subplots(figsize=(3.0,2.6))
labels=["最近出口","拥塞感知"]
vals=[res["gini"]["nearest"],res["gini"]["cong"]]
bars=ax.bar(labels,vals,color=[P["grey"],P["blue"]],edgecolor='white',lw=0.5)
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+0.01,f"{v:.3f}",ha='center',fontsize=8)
ax.set_ylim(0,0.36); ax.set_ylabel("出口流量 Gini 系数")
fig.tight_layout(); fig.savefig(f"{OUT}/图7_均衡度.png"); fig.savefig(f"{OUT}/图7_均衡度.pdf"); plt.close(fig)

# 图8 排队热图
q=np.array(res["q_heat"]["q"])[:150,:]
fig,ax=plt.subplots(figsize=(3.6,2.8))
im=ax.imshow(q.T,aspect='auto',cmap='viridis',origin='lower')
ax.set_xticks(np.arange(0,len(q),20)); ax.set_xticklabels([str(int(i*0.1)) for i in range(0,len(q),20)],fontsize=7)
ax.set_yticks([0,1,2]); ax.set_yticklabels(["E1","E2","E3"])
ax.set_xlabel("时间 / s"); ax.set_ylabel("出口")
cbar=fig.colorbar(im,ax=ax,pad=0.02); cbar.ax.set_ylabel("排队人数",fontsize=8)
fig.tight_layout(); fig.savefig(f"{OUT}/图8_排队热图.png"); fig.savefig(f"{OUT}/图8_排队热图.pdf"); plt.close(fig)

# 图9 复杂度计时
t=res["timing"]; Ns=[int(k) for k in t]; ts=[t[k] for k in t]
fig,ax=plt.subplots(figsize=(3.6,2.6))
ax.plot(Ns,ts,'-o',color=P["blue"],lw=1.8,ms=4)
ax.set_xlabel("人数 N"); ax.set_ylabel("单次仿真耗时 / s")
fig.tight_layout(); fig.savefig(f"{OUT}/图9_复杂度.png"); fig.savefig(f"{OUT}/图9_复杂度.pdf"); plt.close(fig)
print("figs3 done")

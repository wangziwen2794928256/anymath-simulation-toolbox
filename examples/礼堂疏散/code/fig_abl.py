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
P={"navy":"#1F4E79","blue":"#2E75B6","blue2":"#6EA8D8","orange":"#E0863B","green":"#4E9A67",
   "red":"#C0564A","purple":"#7A5FA8","grey":"#9AA0A6","light":"#D8DDE1","dark":"#26282B"}
OUT="例题/礼堂疏散/figures"
D=json.load(open("/tmp/evac_ablation.json"))
fig,axes=plt.subplots(1,2,figsize=(7.2,2.8))
# (a) 重分配频率
ax=axes[0]
freq=list(D["freq"].keys()); vals=[D["freq"][k] for k in freq]
cols=[P["navy"] if v==min(vals) else P["blue2"] for v in vals]
b=ax.bar(freq,vals,color=cols,edgecolor='white',lw=0.5)
for bi,v in zip(b,vals): ax.text(bi.get_x()+bi.get_width()/2,v+8,f"{v:.0f}",ha='center',fontsize=7)
ax.set_ylim(0,470); ax.set_ylabel("总疏散时间 / s"); ax.set_xlabel("重分配频率")
ax.set_xticklabels(freq,rotation=20,fontsize=7)
ax.text(-0.14,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (b) 拥塞权重 λ
ax=axes[1]
lams=[float(k) for k in D["lam"]]; tvals=[D["lam"][str(int(k))] for k in lams]
ax.plot(lams,tvals,'-o',color=P["blue"],lw=1.6,ms=4)
ax.axhline(177.9,color=P["green"],ls='--',lw=0.9,label="最优 λ=5")
ax.set_xlabel("拥塞权重 λ"); ax.set_ylabel("总疏散时间 / s"); ax.legend(loc='upper right')
ax.text(-0.14,1.04,"b",transform=ax.transAxes,fontsize=11,fontweight='bold')
fig.suptitle("图 5  系统化消融（a 重分配频率；b 拥塞权重 λ）",x=0.08,ha='left',fontsize=9,fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.92])
fig.savefig(f"{OUT}/AI图5_消融.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图5_消融.pdf"); plt.close(fig)
print("ablation fig done")

# -*- coding: utf-8 -*-
"""图2 复合组图：方法-颜色映射 + 多样图表类型（曲线/分组柱/横向消融/区域）。"""
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
 'legend.fontsize':7.5,'figure.facecolor':'white','savefig.facecolor':'white','savefig.bbox':'tight'})
# 方法-颜色映射（全图一致）
M={"随机":"#9AA0A6","最近出口":"#C0564A","最短队列":"#E0863B","静态拥塞":"#7A5FA8","动态拥塞(本文)":"#1F4E79","Q学习":"#4E9A67"}
OUT="例题/礼堂疏散/figures"
D=json.load(open("/tmp/evac_deep.json")); E=json.load(open("/tmp/evac_extra.json"))
from evac_sim import run
Rb=[run("nearest",0,s)[2] for s in range(2026,2028)]
Rp=[run("cong",3.0,s)[2] for s in range(2026,2028)]
L=max(len(r) for r in Rb+Rp)
def al(r):
    o=np.full(L,np.nan); o[:len(r)]=r
    for i in range(len(r),L): o[i]=o[i-1]
    return o
Ab=np.array([al(r) for r in Rb]); Ap=np.array([al(r) for r in Rp]); t=np.arange(L)*0.1
fig,axes=plt.subplots(2,2,figsize=(7.4,5.0))
# a 疏散曲线（线+CI）
ax=axes[0,0]
ax.plot(t,Ab.mean(0),color=M["最近出口"],lw=1.6,label="最近出口")
ax.fill_between(t,Ab.mean(0)-Ab.std(0),Ab.mean(0)+Ab.std(0),color=M["最近出口"],alpha=0.12,lw=0)
ax.plot(t,Ap.mean(0),color=M["动态拥塞(本文)"],lw=1.8,label="动态拥塞(本文)")
ax.fill_between(t,Ap.mean(0)-Ap.std(0),Ap.mean(0)+Ap.std(0),color=M["动态拥塞(本文)"],alpha=0.12,lw=0)
ax.set_xlabel("时间/s"); ax.set_ylabel("剩余人数"); ax.legend(loc='upper right')
ax.text(-0.14,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight='bold')
# b 出口流量（分组柱，多色）
ax=axes[0,1]
x=np.arange(3); w=0.36
ax.bar(x-w/2,E["gini"]["nearest_flow"],w,label="最近出口",color=M["最近出口"],edgecolor='white',lw=0.5)
ax.bar(x+w/2,E["gini"]["cong_flow"],w,label="动态拥塞(本文)",color=M["动态拥塞(本文)"],edgecolor='white',lw=0.5)
ax.set_xticks(x); ax.set_xticklabels(["E1","E2","E3"]); ax.set_ylim(0,280); ax.set_xlabel("出口"); ax.set_ylabel("疏散人数/人"); ax.legend(loc='upper right')
ax.text(-0.14,1.04,"b",transform=ax.transAxes,fontsize=11,fontweight='bold')
# c 消融（横向条形 + 贡献差值）
ax=axes[1,0]
labels=["动态(1步)","分段(10步)","分段(40步)","静态"]
vals=[D["abl"]["全程动态(每1步)"],224.7,D["abl"]["分段重分配(每40步)"],D["abl"]["静态最近出口"]]
cols=[M["动态拥塞(本文)"],M["最短队列"],M["静态拥塞"],M["最近出口"]]
yy=np.arange(len(labels))[::-1]
b=ax.barh(yy,vals,color=cols,edgecolor='white',lw=0.5)
for bi,v in zip(b,vals): ax.text(v+6,bi.get_y()+bi.get_height()/2,f"{v:.0f}",va='center',fontsize=7)
ax.set_yticks(yy); ax.set_yticklabels(labels); ax.set_xlim(0,470); ax.set_xlabel("总疏散时间/s"); ax.set_ylabel("重分配机制")
ax.text(-0.14,1.04,"c",transform=ax.transAxes,fontsize=11,fontweight='bold')
# d 密度敏感性（区域+线，双方法）
ax=axes[1,1]
Ns=[200,300,400,500]
ax.plot(Ns,[D["dens_base"][str(n)] for n in Ns],'-o',color=M["最近出口"],ms=3,label="最近出口")
ax.plot(Ns,[D["dens"][str(n)] for n in Ns],'-o',color=M["动态拥塞(本文)"],ms=3,label="动态拥塞(本文)")
ax.fill_between(Ns,[D["dens"][str(n)] for n in Ns],[D["dens_base"][str(n)] for n in Ns],color=M["动态拥塞(本文)"],alpha=0.08)
ax.set_xlabel("人数 N"); ax.set_ylabel("总疏散时间/s"); ax.legend(loc='upper left')
ax.text(-0.14,1.04,"d",transform=ax.transAxes,fontsize=11,fontweight='bold')
fig.tight_layout()
fig.savefig(f"{OUT}/AI图2_复合组图.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图2_复合组图.pdf"); plt.close(fig)
print("fig2 polished")

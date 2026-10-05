# -*- coding: utf-8 -*-
"""礼堂疏散例题配图（按外部 skill 规范：SimHei优先+Nature语义配色+中文标签+复合组图）。"""
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
res=json.load(open("/tmp/evac_results.json"))

# 图1 礼堂平面+出口+人群
rng=np.random.default_rng(1)
pts=[]
for cx,cy,w in [(12,3,0.60),(19,8,0.25),(5,8,0.15)]:
    m=int(round(400*w)); p=rng.normal(loc=(cx,cy),scale=(2.2,1.6),size=(m,2))
    p[:,0]=np.clip(p[:,0],0.5,23.5); p[:,1]=np.clip(p[:,1],0.5,15.5); pts.append(p)
pts=np.concatenate(pts)
fig,ax=plt.subplots(figsize=(5.4,3.6))
ax.add_patch(plt.Rectangle((0,0),24,16,fc='white',ec=P["dark"],lw=1.5))
ax.scatter(pts[:,0],pts[:,1],s=4,color=P["blue"],alpha=0.5,label="人员")
for name,(ex,ey),wd in [("E1",(0,8),1.6),("E2",(24,8),1.2),("E3",(12,0),0.8)]:
    ax.plot(ex,ey,'*',ms=18,color=P["red"],zorder=5)
    ax.text(ex+ (0.6 if ex==0 else -0.6), ey+(0.6 if ey==0 else -0.6), f"{name}\n{wd}m", fontsize=7, color=P["black"], ha='center')
ax.set_xlim(-1,25); ax.set_ylim(-1,17); ax.set_aspect('equal'); ax.set_xlabel("x / m"); ax.set_ylabel("y / m")
ax.legend(loc='upper left')
fig.savefig(f"{OUT}/图1_礼堂平面.png"); fig.savefig(f"{OUT}/图1_礼堂平面.pdf"); plt.close(fig)

# 图2 复合组图 (a) 疏散曲线 (b) 出口流量对比
from evac_sim import run
import sys; sys.path.insert(0,'/tmp')
sys.path.insert(0,'/tmp'); exec(open('/tmp/evac_sim.py').read().split("if __name__")[0])
Rb=[run("nearest",0,s)[2] for s in range(2026,2028)]
Rp=[run("cong",3.0,s)[2] for s in range(2026,2028)]
L=max(len(r) for r in Rb+Rp)
def al(r):
    o=np.full(L,np.nan); o[:len(r)]=r
    for i in range(len(r),L): o[i]=o[i-1]
    return o
Ab=np.array([al(r) for r in Rb]); Ap=np.array([al(r) for r in Rp])
t=np.arange(L)*0.1
fig,ax=plt.subplots(1,2,figsize=(7.2,2.8))
ax0=ax[0]
ax0.plot(t,Ab.mean(0),color=P["grey"],lw=1.8,label="最近出口")
ax0.fill_between(t,Ab.mean(0)-Ab.std(0),Ab.mean(0)+Ab.std(0),color=P["grey"],alpha=0.2,lw=0)
ax0.plot(t,Ap.mean(0),color=P["blue"],lw=1.8,label="拥塞感知")
ax0.fill_between(t,Ap.mean(0)-Ap.std(0),Ap.mean(0)+Ap.std(0),color=P["blue"],alpha=0.2,lw=0)
ax0.set_xlabel("时间 / s"); ax0.set_ylabel("剩余人数"); ax0.legend(loc='upper right')
ax0.text(-0.12,1.04,"a",transform=ax0.transAxes,fontsize=11,fontweight='bold')
ax1=ax[1]
flows=[[round(x) for x in res["nearest_flow"]],[round(x) for x in res["cong_flow"]]]
x=np.arange(3); w=0.36
ax1.bar(x-w/2,flows[0],w,label="最近出口",color=P["grey"],edgecolor='white',lw=0.5)
ax1.bar(x+w/2,flows[1],w,label="拥塞感知",color=P["blue"],edgecolor='white',lw=0.5)
for xi,a,b in zip(x,flows[0],flows[1]):
    ax1.text(xi-w/2,a+5,f"{a}",ha='center',fontsize=7); ax1.text(xi+w/2,b+5,f"{b}",ha='center',fontsize=7)
ax1.set_xticks(x); ax1.set_xticklabels(["E1","E2","E3"]); ax1.set_ylim(0,300)
ax1.set_xlabel("出口"); ax1.set_ylabel("疏散人数 / 人"); ax1.legend(loc='upper right')
ax1.text(-0.12,1.04,"b",transform=ax1.transAxes,fontsize=11,fontweight='bold')
fig.tight_layout(); fig.savefig(f"{OUT}/图2_疏散曲线与流量.png"); fig.savefig(f"{OUT}/图2_疏散曲线与流量.pdf"); plt.close(fig)

# 图3 敏感性 λ
lams=np.arange(0,8.1,1.0)
Ts=[]
for l in lams:
    tt=[]
    for s in range(2026,2030):
        tt.append(run("cong",float(l),s)[0])
    Ts.append(np.mean(tt))
fig,ax=plt.subplots(figsize=(3.6,2.6))
ax.plot(lams,Ts,'-o',color=P["blue"],lw=1.8,ms=4)
ax.axvline(3.0,color=P["red"],ls='--',lw=1,label="取 λ=3")
ax.set_xlabel("拥塞权重 λ"); ax.set_ylabel("总疏散时间 / s"); ax.legend(loc='upper right')
fig.savefig(f"{OUT}/图3_敏感性.png"); fig.savefig(f"{OUT}/图3_敏感性.pdf"); plt.close(fig)
print("figures done")

# -*- coding: utf-8 -*-
"""AI 顶会风成品图：方法总览图 + 复合4面板组图 + 定性2面板。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
for n in ['SimHei','PingFang SC','Songti SC','Heiti SC']:
    try: fm.fontManager.addfont(fm.findfont(n, fallback_to_default=False))
    except Exception: pass
plt.rcParams['font.family']='sans-serif'
plt.rcParams['font.sans-serif']=['SimHei','PingFang SC','Songti SC','Arial']
plt.rcParams['axes.unicode_minus']=False
plt.rcParams.update({'axes.spines.right':False,'axes.spines.top':False,'legend.frameon':False,
 'axes.linewidth':0.8,'figure.dpi':300,'savefig.dpi':300,'font.size':9,'axes.labelsize':9,
 'legend.fontsize':7.5,'figure.facecolor':'white','savefig.facecolor':'white','savefig.bbox':'tight'})
C={"blue":"#0F4D92","blue2":"#3775BA","green":"#8BCF8B","red":"#B64342","grey":"#9AA0A6","light":"#CFCECE","dark":"#3C4043","bg":"#F1F3F4"}
OUT="例题/礼堂疏散/figures"
res=json.load(open("/tmp/evac_deep.json"))
extra=json.load(open("/tmp/evac_extra.json"))

def box(ax,x,y,w,h,txt,ec,fc="#F4F6F8",fs=8,lw=1.1,title=None):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.06",
                 linewidth=lw,edgecolor=ec,facecolor=fc))
    lines=txt.split("\n")
    n=len(lines); ys=y+h-0.18
    if title:
        ax.text(x+w/2,y+h-0.16,title,ha='center',va='center',fontsize=fs,fontweight='bold',color=ec)
        ys=y+h-0.38; lines=txt.split("\n")
    for i,ln in enumerate(lines):
        ax.text(x+w/2, ys-i*0.24, ln, ha='center',va='center',fontsize=fs-0.7,color=C["dark"])
def arr(ax,p0,p1,color=C["dark"],lw=1.2,style="-|>",ls='-'):
    ax.add_patch(FancyArrowPatch(p0,p1,arrowstyle=style,mutation_scale=12,color=color,lw=lw,linestyle=ls))

# ===== 图1 方法总览图 =====
fig,ax=plt.subplots(figsize=(7.2,4.2)); ax.set_xlim(0,14); ax.set_ylim(0,8.6); ax.axis("off")
ax.text(7,8.3,"图 1  方法总览：多智能体疏散系统的环境—智能体—协同—服务闭环",ha='center',fontsize=9.5,fontweight='bold')
box(ax,4,6.6,6,1.3,"礼堂 24 m×16 m；出口 E={e1,e2,e3}，宽 1.6/1.2/0.8 m",C["dark"],C["bg"],8)
ax.text(7,7.55,"环境 S",ha='center',fontsize=7,color=C["dark"],fontweight='bold')
box(ax,4,4.9,6,1.3,"N=400；状态 p_i=(x_i,y_i)；观测 O_i=(p_i,{Q_e})；策略 π_i(a_i|o_i)",C["blue"],C["bg"],8)
ax.text(7,5.85,"智能体 i",ha='center',fontsize=7,color=C["blue"],fontweight='bold')
box(ax,4,3.2,6,1.3,"代价 c_i(e)=d_i(e)+λQ_e(t)；出口分配 a_i=argmin_e c_i(e)",C["blue"],C["bg"],8)
ax.text(7,4.15,"协同算法（拥塞感知）",ha='center',fontsize=7,color=C["blue"],fontweight='bold')
box(ax,4,1.5,6,1.3,"容量 w_e·q=0.73 人/(m·s)；FIFO 队列；离场计数",C["red"],C["bg"],8)
ax.text(7,2.45,"出口服务",ha='center',fontsize=7,color=C["red"],fontweight='bold')
for y0,y1 in [(6.6,6.2),(4.9,4.5),(3.2,2.8)]:
    arr(ax,(7,y0),(7,y1),C["dark"],1.3)
# 反馈回路（右侧）
arr(ax,(10.15,2.15),(12.6,2.15),C["red"],1.1)
arr(ax,(12.6,2.15),(12.6,3.85),C["red"],1.1)
arr(ax,(12.6,3.85),(10.15,3.85),C["red"],1.1,style="-|>")
ax.text(11.6,3.0,"Q_e 实时反馈",ha='center',fontsize=7,color=C["red"])
# 输入/输出标注
ax.text(1.6,7.25,"输入\n人数/速度/比流量",ha='center',fontsize=6.8,color=C["grey"])
arr(ax,(2.4,7.25),(4.0,7.25),C["grey"],0.9)
ax.text(11.0,1.0,"输出\n总疏散时间 T",ha='center',fontsize=6.8,color=C["grey"])
arr(ax,(9.0,1.55),(10.4,1.1),C["grey"],0.9)
fig.savefig(f"{OUT}/AI图1_方法总览.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图1_方法总览.pdf"); plt.close(fig)

# ===== 图2 复合4面板组图 =====
# 复算曲线（最近出口 vs 拥塞感知，10 seeds 均值±std 的剩余人数）
def run_trace(policy,lam,seed,N=400):
    np.random.seed(seed)
    import sys; sys.path.insert(0,'/tmp')
    from evac_sim import run
    return run(policy,lam,seed)[2]
Rb=[run_trace("nearest",0,s) for s in range(2026,2031)]
Rp=[run_trace("cong",3.0,s) for s in range(2026,2031)]
L=max(len(r) for r in Rb+Rp)
def al(r):
    o=np.full(L,np.nan); o[:len(r)]=r
    for i in range(len(r),L): o[i]=o[i-1]
    return o
Ab=np.array([al(r) for r in Rb]); Ap=np.array([al(r) for r in Rp])
t=np.arange(L)*0.1
fig,axes=plt.subplots(2,2,figsize=(7.2,5.0))
# (a)
ax=axes[0,0]
ax.plot(t,Ab.mean(0),color=C["grey"],lw=1.6,label="最近出口")
ax.fill_between(t,Ab.mean(0)-Ab.std(0),Ab.mean(0)+Ab.std(0),color=C["grey"],alpha=0.15,lw=0)
ax.plot(t,Ap.mean(0),color=C["blue"],lw=1.6,label="拥塞感知")
ax.fill_between(t,Ap.mean(0)-Ap.std(0),Ap.mean(0)+Ap.std(0),color=C["blue"],alpha=0.15,lw=0)
ax.set_xlabel("时间 / s"); ax.set_ylabel("剩余人数"); ax.legend(loc='upper right')
ax.text(-0.14,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (b)
ax=axes[0,1]
x=np.arange(3); w=0.36
ax.bar(x-w/2,extra["gini"]["nearest_flow"],w,label="最近出口",color=C["grey"],edgecolor='white',lw=0.5)
ax.bar(x+w/2,extra["gini"]["cong_flow"],w,label="拥塞感知",color=C["blue"],edgecolor='white',lw=0.5)
ax.set_xticks(x); ax.set_xticklabels(["E1","E2","E3"]); ax.set_ylim(0,280)
ax.set_xlabel("出口"); ax.set_ylabel("疏散人数 / 人"); ax.legend(loc='upper right')
ax.text(-0.14,1.04,"b",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (c) 消融
ax=axes[1,0]
labels=["静态","分段(40步)","动态(1步)"]
vals=[res["abl"]["静态最近出口"],res["abl"]["分段重分配(每40步)"],res["abl"]["全程动态(每1步)"]]
cols=[C["grey"],C["blue2"],C["blue"]]
b=ax.bar(labels,vals,color=cols,edgecolor='white',lw=0.5)
for bi,v in zip(b,vals): ax.text(bi.get_x()+bi.get_width()/2,v+8,f"{v:.0f}",ha='center',fontsize=7)
ax.set_ylim(0,480); ax.set_ylabel("总疏散时间 / s"); ax.set_xlabel("分配机制")
ax.text(-0.14,1.04,"c",transform=ax.transAxes,fontsize=11,fontweight='bold')
# (d) 密度敏感性
ax=axes[1,1]
Ns=[200,300,400,500]
ax.plot(Ns,[res["dens_base"][str(n)] for n in Ns],'-o',color=C["grey"],label="最近出口",ms=3)
ax.plot(Ns,[res["dens"][str(n)] for n in Ns],'-o',color=C["blue"],label="拥塞感知",ms=3)
ax.set_xlabel("人数 N"); ax.set_ylabel("总疏散时间 / s"); ax.legend(loc='upper left')
ax.text(-0.14,1.04,"d",transform=ax.transAxes,fontsize=11,fontweight='bold')
fig.tight_layout()
fig.savefig(f"{OUT}/AI图2_复合组图.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图2_复合组图.pdf"); plt.close(fig)

# ===== 图3 定性2面板（排队热图 + 均衡度）=====
fig,axes=plt.subplots(1,2,figsize=(7.2,2.8))
q=np.array(extra["q_heat"]["q"])[:150,:]
ax=axes[0]
im=ax.imshow(q.T,aspect='auto',cmap='viridis',origin='lower')
ax.set_xticks(np.arange(0,len(q),20)); ax.set_xticklabels([str(int(i*0.1)) for i in range(0,len(q),20)],fontsize=7)
ax.set_yticks([0,1,2]); ax.set_yticklabels(["E1","E2","E3"])
ax.set_xlabel("时间 / s"); ax.set_ylabel("出口")
cbar=fig.colorbar(im,ax=ax,pad=0.02); cbar.ax.set_ylabel("排队人数",fontsize=7)
ax.text(-0.14,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight='bold')
ax=axes[1]
b=ax.bar(["最近出口","拥塞感知"],[extra["gini"]["nearest"],extra["gini"]["cong"]],color=[C["grey"],C["blue"]],edgecolor='white',lw=0.5)
for bi,v in zip(b,[extra["gini"]["nearest"],extra["gini"]["cong"]]): ax.text(bi.get_x()+bi.get_width()/2,v+0.008,f"{v:.3f}",ha='center',fontsize=8)
ax.set_ylim(0,0.36); ax.set_ylabel("出口流量 Gini 系数")
ax.text(-0.14,1.04,"b",transform=ax.transAxes,fontsize=11,fontweight='bold')
fig.tight_layout()
fig.savefig(f"{OUT}/AI图3_定性.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图3_定性.pdf"); plt.close(fig)
print("AI figures done")

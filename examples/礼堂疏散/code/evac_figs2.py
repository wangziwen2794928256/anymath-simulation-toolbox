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
res=json.load(open("/tmp/evac_deep.json"))

def box(ax,x,y,w,h,txt,ec,fc="#EEF3FA",fs=8):
    ax.add_patch(plt.Rectangle((x,y),w,h,fc=fc,ec=ec,lw=1))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,color=P["black"])
def arrow(ax,p0,p1,c=P["dark"]):
    ax.annotate("",xy=p1,xytext=p0,arrowprops=dict(arrowstyle="-|>",color=c,lw=1))

# 图2 多智能体形式化示意图
fig,ax=plt.subplots(figsize=(7.2,3.2)); ax.set_xlim(0,14); ax.set_ylim(0,5.6); ax.axis("off")
box(ax,0.5,3.6,4.2,1.5,"环境 E\n礼堂空间 S · 出口集合 E\n转移 P(s'|s,a)",P["dark"],"#F2F2F2")
box(ax,6.0,3.6,3.6,1.5,"智能体 i\n(Oi, Ai, πi)\n位置 · 观测 · 策略",P["blue"])
box(ax,10.4,3.6,3.2,1.5,"出口服务\n队列 · 容量 w·q",P["red"],"#FBEAEA")
box(ax,6.0,1.0,3.6,1.2,"交互拓扑 G(V,E)\n全共享排队信息",P["blue2"])
arrow(ax,(2.6,3.6),(6.0,3.6)); arrow(ax,(7.8,3.6),(10.4,3.6))
arrow(ax,(7.8,3.6),(7.8,2.2)); arrow(ax,(6.0,1.6),(3.2,3.6))
ax.text(7.0,5.2,"图 2  多智能体系统形式化：环境–智能体–出口服务–交互拓扑",ha='center',fontsize=9)
fig.savefig(f"{OUT}/图2_形式化.png"); fig.savefig(f"{OUT}/图2_形式化.pdf"); plt.close(fig)

# 图3 算法流程图
fig,ax=plt.subplots(figsize=(3.6,4.6)); ax.set_xlim(0,10); ax.set_ylim(0,12); ax.axis("off")
steps=["初始化 400 人位置","t=0","出口服务(容量 w·q·Δt)","计算代价 d+λ·Q","重分配出口 a_i","朝出口移动 v·Δt","到达→入队","全部离场?","输出总疏散时间"]
ys=[11,10,8.6,7.2,5.8,4.4,3.0,1.6,0.4]
for i,(s,y) in enumerate(zip(steps,ys)):
    ec=P["blue"] if i in (3,4) else P["dark"]
    box(ax,3,y,4,0.75,s,ec,fs=7)
    if i<len(steps)-1:
        arrow(ax,(5,y),(5,y-0.62))
ax.text(5,11.8,"算法 1  拥塞感知动态分配",ha='center',fontsize=9)
fig.savefig(f"{OUT}/图3_算法流程.png"); fig.savefig(f"{OUT}/图3_算法流程.pdf"); plt.close(fig)

# 图5 消融
fig,ax=plt.subplots(figsize=(3.8,2.8))
labels=["静态最近出口","分段重分配\n(每40步)","全程动态\n(每1步)"]
vals=[res["abl"]["静态最近出口"],res["abl"]["分段重分配(每40步)"],res["abl"]["全程动态(每1步)"]]
colors=[P["grey"],P["blue2"],P["blue"]]
bars=ax.bar(labels,vals,color=colors,edgecolor='white',lw=0.5)
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+8,f"{v:.0f}",ha='center',fontsize=8)
ax.set_ylim(0,480); ax.set_ylabel("总疏散时间 / s")
ax.text(-0.12,1.04,"a",transform=ax.transAxes,fontsize=11,fontweight='bold')
fig.tight_layout(); fig.savefig(f"{OUT}/图5_消融.png"); fig.savefig(f"{OUT}/图5_消融.pdf"); plt.close(fig)

# 图6 敏感性复合组图
fig,ax=plt.subplots(1,2,figsize=(7.2,2.8))
ax0=ax[0]
Ns=[200,300,400,500]
ax0.plot(Ns,[res["dens_base"][str(n)] for n in Ns],'-o',color=P["grey"],label="最近出口")
ax0.plot(Ns,[res["dens"][str(n)] for n in Ns],'-o',color=P["blue"],label="拥塞感知")
ax0.set_xlabel("人数 N"); ax0.set_ylabel("总疏散时间 / s"); ax0.legend(loc='upper left')
ax0.text(-0.12,1.04,"a",transform=ax0.transAxes,fontsize=11,fontweight='bold')
ax1=ax[1]
vs=[1.0,1.2,1.34,1.5,1.6]
ax1.plot(vs,[res["speed"][str(v)] for v in vs],'-s',color=P["blue"])
ax1.axhline(400/(1.6+1.2+0.8)/0.73,color=P["red"],ls='--',lw=1,label="理论下限")
ax1.set_xlabel("行走速度 / (m/s)"); ax1.set_ylabel("总疏散时间 / s"); ax1.legend(loc='upper left')
ax1.text(-0.12,1.04,"b",transform=ax1.transAxes,fontsize=11,fontweight='bold')
fig.tight_layout(); fig.savefig(f"{OUT}/图6_敏感性.png"); fig.savefig(f"{OUT}/图6_敏感性.pdf"); plt.close(fig)
print("figs2 done")

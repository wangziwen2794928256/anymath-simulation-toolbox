# -*- coding: utf-8 -*-
"""重做图1（三列：环境|智能体|算法，配色重做）+ 训练曲线图。"""
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
 'legend.fontsize':8,'figure.facecolor':'white','savefig.facecolor':'white','savefig.bbox':'tight'})
# 重做配色：高对比、区分度强
P={"navy":"#1F4E79","blue":"#2E75B6","blue2":"#6EA8D8","orange":"#E0863B","green":"#4E9A67",
   "red":"#C0564A","purple":"#7A5FA8","grey":"#9AA0A6","light":"#D8DDE1","dark":"#26282B","bg":"#F5F7F9"}
OUT="例题/礼堂疏散/figures"

def box(ax,x,y,w,h,title,body,ec,fc=None,fs=7.5,tfs=8):
    fc=fc or P["bg"]
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.05",
                 linewidth=1.2,edgecolor=ec,facecolor=fc))
    ax.text(x+w/2,y+h-0.14,title,ha='center',va='center',fontsize=tfs,fontweight='bold',color=ec)
    if body:
        ax.text(x+w/2,y+h-0.14-0.20,body,ha='center',va='top',fontsize=fs,color=P["dark"])
def arr(ax,p0,p1,c=P["dark"],lw=1.3,style="-|>",ls='-'):
    ax.add_patch(FancyArrowPatch(p0,p1,arrowstyle=style,mutation_scale=11,color=c,lw=lw,linestyle=ls))

# ============ 图1 方法总览（三列分离）============
fig,ax=plt.subplots(figsize=(7.4,3.8)); ax.set_xlim(0,15); ax.set_ylim(0,7.8); ax.axis("off")
ax.text(7.5,7.5,"图 1  方法总览：环境—智能体—算法三体分离，算法含状态编码·策略·分配·反馈四子模块",ha='center',fontsize=9.5,fontweight='bold',color=P["dark"])
# 环境列
box(ax,0.3,2.6,3.2,3.2,"环境 E","礼堂 S⊂R²\n出口 {e₁,e₂,e₃}\n宽度 1.6/1.2/0.8 m\n比流量 q=0.73",P["navy"],fs=7)
# 智能体列
box(ax,4.2,2.6,3.2,3.2,"智能体 i（N=400）","状态 pᵢ=(xᵢ,yᵢ)\n观测 Oᵢ=(pᵢ,{Qₑ})\n策略 πᵢ(aᵢ|oᵢ)\n速度 v₀=1.34",P["blue"],fs=7)
# 算法列（含四子模块）
box(ax,8.1,2.6,3.6,3.2,"协同算法","",P["orange"])
subs=["状态编码\n(dᵢ,Qₑ)","策略\ncᵢ(e)=dᵢ+λQₑ","分配\naᵢ=argmin cᵢ","反馈\nQₑ 回传"]
for i,t in enumerate(subs):
    bx=8.25+i*0.85; by=2.85+i*0.62
    ax.add_patch(FancyBboxPatch((bx,by),0.78,0.52,boxstyle="round,pad=0.01,rounding_size=0.04",
                 linewidth=0.9,edgecolor=P["orange"],facecolor="#FDF3E7"))
    ax.text(bx+0.39,by+0.26,t,ha='center',va='center',fontsize=5.6,color=P["dark"])
# 输出
box(ax,12.0,1.1,2.6,1.0,"输出","总疏散时间 T\n吞吐/Gini/流量",P["green"],fs=7)
# 箭头
arr(ax,(3.5,4.2),(4.2,4.2)); arr(ax,(7.4,4.2),(8.1,4.2))
arr(ax,(9.9,2.6),(11.2,2.1),P["green"],1.1)
arr(ax,(11.5,2.6),(3.6,4.0),P["red"],0.9,ls=(0,(4,2)))  # 反馈
ax.text(7.0,3.35,"Qₑ 环境反馈",ha='center',fontsize=6.5,color=P["red"])
fig.savefig(f"{OUT}/AI图1_方法总览.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图1_方法总览.pdf"); plt.close(fig)

# ============ 图4 训练曲线（Q学习）============
D=json.load(open("/tmp/dqn_results.json"))
m=np.array(D["curve_mean"]); s=np.array(D["curve_std"]); ep=np.arange(len(m))
fig,ax=plt.subplots(figsize=(3.6,2.7))
ax.plot(ep,m,color=P["blue"],lw=1.6,label="Q学习")
ax.fill_between(ep,m-s,m+s,color=P["blue"],alpha=0.15,lw=0)
ax.set_xlabel("训练回合"); ax.set_ylabel("回合累计奖励"); ax.set_title("图 4  学习式方法的训练曲线",loc='left',fontsize=8.5,fontweight='bold')
ax.legend(loc='lower right')
fig.tight_layout(); fig.savefig(f"{OUT}/AI图4_训练曲线.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图4_训练曲线.pdf"); plt.close(fig)
print("fig_fix done")

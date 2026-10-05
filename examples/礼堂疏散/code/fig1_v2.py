# -*- coding: utf-8 -*-
"""图1 v2：三层信息架构（环境层/智能体层/算法层），清晰标题+正文分离，无文字重叠。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
for n in ['SimHei','PingFang SC','Songti SC','Heiti SC']:
    try: fm.fontManager.addfont(fm.findfont(n, fallback_to_default=False))
    except Exception: pass
plt.rcParams['font.family']='sans-serif'
plt.rcParams['font.sans-serif']=['SimHei','PingFang SC','Songti SC','Arial']
plt.rcParams['axes.unicode_minus']=False
P={"navy":"#1F4E79","blue":"#2E75B6","blue2":"#6EA8D8","orange":"#E0863B","green":"#4E9A67",
   "red":"#C0564A","purple":"#7A5FA8","grey":"#9AA0A6","light":"#D8DDE1","dark":"#26282B","bg":"#F5F7F9"}
OUT="例题/礼堂疏散/figures"

def hdr(ax,x,y,w,txt,color):
    ax.text(x+w/2,y,txt,ha='center',va='center',fontsize=8,fontweight='bold',color=color)
def block(ax,x,y,w,h,txt,ec,fc="#F5F7F9",fs=7):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.05",linewidth=1.1,edgecolor=ec,facecolor=fc))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,color=P["dark"])
def arrow(ax,p0,p1,c=P["dark"],lw=1.2,ls='-',style="-|>"):
    ax.add_patch(FancyArrowPatch(p0,p1,arrowstyle=style,mutation_scale=11,color=c,lw=lw,linestyle=ls))

fig,ax=plt.subplots(figsize=(7.6,4.2)); ax.set_xlim(0,16); ax.set_ylim(0,8.6); ax.axis("off")
ax.text(8,8.25,"图 1  方法总览：环境—智能体—算法三层架构与闭环反馈",ha='center',fontsize=9.5,fontweight='bold',color=P["dark"])

# 环境层
hdr(ax,0.3,7.0,3.4,"环境层 Environment",P["navy"])
block(ax,0.3,5.5,3.4,1.3,"礼堂 S⊂R²\n出口 {e₁,e₂,e₃}\n宽度 1.6/1.2/0.8 m",P["navy"],fs=7)
# 智能体层
hdr(ax,0.3,4.6,3.4,"智能体层 Agent",P["blue"])
block(ax,0.3,3.1,3.4,1.3,"N=400 智能体\n状态 pᵢ=(xᵢ,yᵢ)\n观测 Oᵢ=(pᵢ,{Qₑ})",P["blue"],fs=7)
# 算法层（右侧大块，含4步流水线）
hdr(ax,5.2,7.0,10.5,"算法层 Algorithm（拥塞感知协同）",P["orange"])
steps=[("状态编码", "(dᵢ,Qₑ)",P["blue2"]),("代价计算","cᵢ(e)=dᵢ+λQₑ",P["orange"]),
       ("出口分配","aᵢ=argmin cᵢ",P["orange"]),("全局反馈","Qₑ 回传",P["red"])]
for i,(t,sub,c) in enumerate(steps):
    x=5.5+i*2.6
    block(ax,x,5.5,2.4,0.75,t,c,fs=7)
    ax.text(x+1.2,5.15,sub,ha='center',va='center',fontsize=6.5,color=P["dark"])
    if i<3: arrow(ax,(x+2.4,5.875),(x+2.55,5.875),P["dark"],1.0)
# 输出块
block(ax,12.6,3.1,2.9,1.0,"输出\n总疏散时间 T",P["green"],fs=7)
# 主流程箭头
arrow(ax,(3.7,6.15),(5.4,6.15),P["navy"],1.1)          # 环境→算法(服务容量)
arrow(ax,(3.7,3.75),(5.4,6.0),P["blue"],1.1)           # 智能体→算法(状态)
arrow(ax,(13.0,4.1),(11.2,5.5),P["green"],1.1)         # 输出
# 反馈闭环（算法→环境）
arrow(ax,(9.5,5.5),(9.5,3.1),P["red"],0.9,ls=(0,(4,2)))  # 向下
ax.text(9.8,4.2,"分配 aᵢ 作用于环境",ha='center',fontsize=6.2,color=P["red"],rotation=90)
# 环境→智能体 观测
arrow(ax,(2.0,5.5),(2.0,4.4),P["blue2"],0.9)
ax.text(2.25,4.95,"观测",ha='left',fontsize=6.2,color=P["blue2"])
# 反馈回算法
arrow(ax,(2.0,3.1),(2.0,1.2),P["red"],0.9,ls=(0,(4,2)))
ax.text(2.25,2.0,"Qₑ 排队反馈",ha='left',fontsize=6.2,color=P["red"])
arrow(ax,(2.0,1.2),(8.0,5.5),P["red"],0.9,ls=(0,(4,2)))
fig.savefig(f"{OUT}/AI图1_方法总览.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图1_方法总览.pdf"); plt.close(fig)
print("fig1 v2 done")

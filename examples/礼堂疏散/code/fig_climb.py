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
M={"IQL":"#C0564A","QMIX":"#1F4E79"}
D=json.load(open("/tmp/climbing.json"))
OUT="例题/礼堂疏散/figures"
fig,ax=plt.subplots(figsize=(3.6,2.7))
for a in ["iql","qmix"]:
    c=np.array(D[a]["curve_mean"]); x=np.arange(len(c))*20
    ax.plot(x,c,color=M[a.upper()],lw=1.6,label=a.upper())
ax.axhline(11,color="#4E9A67",ls='--',lw=0.9,label="最优 11")
ax.axhline(7,color="#E0863B",ls='--',lw=0.9,label="次优 7")
ax.set_xlabel("训练回合"); ax.set_ylabel("共同收益"); ax.set_title("图 6  Climbing Game：IQL vs QMIX",loc='left',fontsize=8.5,fontweight='bold')
ax.legend(loc='lower right',fontsize=7)
fig.tight_layout(); fig.savefig(f"{OUT}/AI图6_climbing.png",dpi=300,bbox_inches='tight'); fig.savefig(f"{OUT}/AI图6_climbing.pdf"); plt.close(fig)
print("climbing fig done")

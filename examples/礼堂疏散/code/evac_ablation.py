# -*- coding: utf-8 -*-
"""系统化消融：重分配频率轴 + 拥塞权重 λ 轴。"""
import numpy as np, json
from collections import deque
W,H=24.0,16.0
EXITS=[(0.0,8.0,1.6),(24.0,8.0,1.2),(12.0,0.0,0.8)]
V0=1.34; FLOW=0.73; DT=0.1; MAXT=1200.0

def make_positions(seed,N=400):
    rng=np.random.default_rng(seed); parts=[]
    for cx,cy,w in [(12,3,0.60),(19,8,0.25),(5,8,0.15)]:
        m=int(round(N*w)); p=rng.normal(loc=(cx,cy),scale=(2.2,1.6),size=(m,2))
        p[:,0]=np.clip(p[:,0],0.5,W-0.5); p[:,1]=np.clip(p[:,1],0.5,H-0.5); parts.append(p)
    return np.concatenate(parts)[:N].copy()

def run(lam, reassign, seed):
    rng=np.random.default_rng(seed); pos=make_positions(seed)
    assign=np.full(400,-1,int); arrived=np.zeros(400,bool); departed=np.zeros(400,bool); dep_t=np.full(400,-1.0)
    queues=[deque() for _ in range(3)]; frac=[0.0]*3; flow=[0,0,0]
    for k in range(int(MAXT/DT)+1):
        t=k*DT
        for e in range(3):
            frac[e]+=EXITS[e][2]*FLOW*DT; no=int(frac[e])
            for _ in range(no):
                if queues[e]: i=queues[e].popleft(); departed[i]=True; dep_t[i]=t; flow[e]+=1
            frac[e]-=no
        if departed.all(): break
        d=np.stack([np.hypot(pos[:,0]-EXITS[e][0],pos[:,1]-EXITS[e][1]) for e in range(3)],1)
        if reassign is None:
            assign[assign<0]=np.argmin(d,1)[assign<0]
        else:
            if k%reassign==0:
                cost=d+lam*np.array([len(queues[e]) for e in range(3)])[None,:]
                assign[~arrived]=np.argmin(cost,1)[~arrived]
            elif assign[0]<0:
                assign[assign<0]=np.argmin(d,1)[assign<0]
        moving=~arrived&~departed
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][0],EXITS[e][1]; dx=ex-pos[ee,0]; dy=ey-pos[ee,1]; dist=np.hypot(dx,dy); s=V0*DT
            pos[ee,0]+=np.where(dist>1e-6,dx/dist*s,0); pos[ee,1]+=np.where(dist>1e-6,dy/dist*s,0)
            pos[ee,0]=np.clip(pos[ee,0],0,W); pos[ee,1]=np.clip(pos[ee,1],0,H)
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][0],EXITS[e][1]; at=np.hypot(pos[ee,0]-ex,pos[ee,1]-ey)<0.5
            if at.any():
                for i in np.where(ee)[0][at]: queues[e].append(int(i)); arrived[i]=True
    return (dep_t.max() if departed.all() else MAXT)

seeds=list(range(2026,2031))
# 频率轴
freq=[None,100,40,10,1]
freq_T={('静态' if f is None else f'每{f}步'): round(float(np.mean([run(3.0,f,s) for s in seeds])),1) for f in freq}
# λ 轴（动态，每1步）
lams=[0,1,2,3,5,8]
lam_T={str(l): round(float(np.mean([run(float(l),1,s) for s in seeds])),1) for l in lams}
json.dump({"freq":freq_T,"lam":lam_T},open("/tmp/evac_ablation.json","w"),ensure_ascii=False,indent=2)
print("freq:",freq_T)
print("lam:",lam_T)

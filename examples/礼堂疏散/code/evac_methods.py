# -*- coding: utf-8 -*-
"""6 方法对比：随机/最近出口/最短队列/静态拥塞/动态拥塞/Q学习。"""
import numpy as np, json
from collections import deque
from dqn_exit import feat  # 复用特征
W,H=24.0,16.0
EXITS=[(0.0,8.0,1.6),(24.0,8.0,1.2),(12.0,0.0,0.8)]
V0=1.34; FLOW=0.73; DT=0.1; MAXT=1200.0

def make_positions(seed,N=400):
    rng=np.random.default_rng(seed); parts=[]
    for cx,cy,w in [(12,3,0.60),(19,8,0.25),(5,8,0.15)]:
        m=int(round(N*w)); p=rng.normal(loc=(cx,cy),scale=(2.2,1.6),size=(m,2))
        p[:,0]=np.clip(p[:,0],0.5,W-0.5); p[:,1]=np.clip(p[:,1],0.5,H-0.5); parts.append(p)
    return np.concatenate(parts)[:N].copy()

def run(N, method, wq=None, lam=3.0, seed=2026):
    rng=np.random.default_rng(seed); pos=make_positions(seed,N)
    assign=np.full(N,-1,int); arrived=np.zeros(N,bool); departed=np.zeros(N,bool); dep_t=np.full(N,-1.0)
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
        qlen=np.array([len(queues[e]) for e in range(3)])
        if method=="random":
            assign[assign<0]=rng.integers(0,3,size=(assign<0).sum())
        elif method=="nearest":
            assign[assign<0]=np.argmin(d,1)[assign<0]
        elif method=="shortest_queue":
            idx=np.where(assign<0)[0]
            for i in idx:
                cands=np.where(qlen==qlen.min())[0]
                assign[i]=cands[np.argmin(d[i,cands])]
        elif method=="static_cong":
            cost=d+lam*qlen[None,:]
            assign[assign<0]=np.argmin(cost,1)[assign<0]
        elif method=="dynamic_cong":
            cost=d+lam*qlen[None,:]
            assign[~arrived]=np.argmin(cost,1)[~arrived]
        elif method=="ql":
            idx=np.where(~arrived)[0]
            if len(idx):
                dd=d[idx]/24.0
                qq=np.tile(qlen.astype(float)/15.0,(len(idx),1))
                F=np.concatenate([dd,qq],axis=1)   # (n,6)
                assign[idx]=np.argmax(F@wq.T,axis=1)
        moving=~arrived&~departed
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][0],EXITS[e][1]
            dx=ex-pos[ee,0]; dy=ey-pos[ee,1]; dist=np.hypot(dx,dy); s=V0*DT
            pos[ee,0]+=np.where(dist>1e-6,dx/dist*s,0); pos[ee,1]+=np.where(dist>1e-6,dy/dist*s,0)
            pos[ee,0]=np.clip(pos[ee,0],0,W); pos[ee,1]=np.clip(pos[ee,1],0,H)
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][0],EXITS[e][1]
            at=np.hypot(pos[ee,0]-ex,pos[ee,1]-ey)<0.5
            if at.any():
                for i in np.where(ee)[0][at]: queues[e].append(int(i)); arrived[i]=True
    return (dep_t.max() if departed.all() else MAXT), flow

def gini(x):
    x=np.sort(np.asarray(x,dtype=float)); n=len(x)
    return (2*np.sum(np.arange(1,n+1)*x)-(n+1)*np.sum(x))/(n*np.sum(x)) if x.sum()>0 else 0

# 加载 Q 学习权重
import importlib.util
spec=importlib.util.spec_from_file_location("dqn_exit","/tmp/dqn_exit.py")
dqn=importlib.util.module_from_spec(spec)
# 避免重新训练：直接重新训练一个 seed
import sys
rng=np.random.default_rng(1)
# 重新训练并取 w
def train_linear(seed,episodes=1500):
    import numpy as np
    rng=np.random.default_rng(seed); w=rng.normal(0,0.1,(3,6)).astype(np.float32); eps=1.0
    for ep in range(episodes):
        pos=(float(rng.uniform(2,22)),float(rng.uniform(2,14))); q=[0.0]*3; done=False; st=0
        while not done and st<600:
            s=feat(pos,q)
            a=int(rng.integers(0,3)) if rng.random()<eps else int(np.argmax(w@s))
            q=[min(15.0,max(0.0,q[e]+(1.0 if e==a else 0.0)-0.35)) for e in range(3)]
            import math
            ex,ey=EXITS[a][0],EXITS[a][1]; dx=ex-pos[0]; dy=ey-pos[1]; dist=np.hypot(dx,dy)
            if dist<0.4: done=True; r=0.0
            else:
                pos=(pos[0]+dx/dist*0.134, pos[1]+dy/dist*0.134); r=-0.1
            s2=feat(pos,q); td=r+0.98*float((w@s2).max())-float(w[a]@s); w[a]+=0.02*td*s; st+=1
        eps=max(0.05,eps*0.996)
    return w

wq=train_linear(7)

res={}
for name in ["random","nearest","shortest_queue","static_cong","dynamic_cong","ql"]:
    T=[]; F=[]
    kw=wq if name=="ql" else None
    for s in range(2026,2031):
        t,f=run(400,name,kw,3.0,s); T.append(t); F.append(f)
    res[name]={"T":round(float(np.mean(T)),1),"Tstd":round(float(np.std(T)),1),
               "flow":[int(round(x)) for x in np.mean(F,axis=0)],"gini":round(gini(np.mean(F,axis=0)),3),
               "thr":round(400/max(np.mean(T),1),3)}
json.dump(res,open("/tmp/evac_methods.json","w"),ensure_ascii=False,indent=2)
for k,v in res.items(): print(k, v["T"], v["flow"], v["gini"])

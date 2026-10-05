# -*- coding: utf-8 -*-
"""补充数据：5智能体算例、Gini均衡度、排队热图、复杂度计时。"""
import numpy as np, json, time
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

def run(N, policy, lam, speed=1.34, seed=2026, trace_q=False):
    rng=np.random.default_rng(seed); pos=make_positions(seed,N)
    assign=np.full(N,-1,int); arrived=np.zeros(N,bool); departed=np.zeros(N,bool); dep_t=np.full(N,-1.0)
    queues=[deque() for _ in range(3)]; frac=[0.0]*3; flow=[0,0,0]; qhist=[]
    for k in range(int(MAXT/DT)+1):
        t=k*DT
        for e in range(3):
            frac[e]+=EXITS[e][2]*FLOW*DT; no=int(frac[e])
            for _ in range(no):
                if queues[e]: i=queues[e].popleft(); departed[i]=True; dep_t[i]=t; flow[e]+=1
            frac[e]-=no
        if departed.all(): break
        d=np.stack([np.hypot(pos[:,0]-EXITS[e][0],pos[:,1]-EXITS[e][1]) for e in range(3)],1)
        if policy=="nearest":
            assign[assign<0]=np.argmin(d,1)[assign<0]
        else:
            cost=d+lam*np.array([len(queues[e]) for e in range(3)])[None,:]
            assign[~arrived]=np.argmin(cost,1)[~arrived]
        moving=~arrived&~departed
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][0],EXITS[e][1]
            dx=ex-pos[ee,0]; dy=ey-pos[ee,1]; dist=np.hypot(dx,dy); s=speed*DT
            pos[ee,0]+=np.where(dist>1e-6,dx/dist*s,0); pos[ee,1]+=np.where(dist>1e-6,dy/dist*s,0)
            pos[ee,0]=np.clip(pos[ee,0],0,W); pos[ee,1]=np.clip(pos[ee,1],0,H)
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][0],EXITS[e][1]
            at=np.hypot(pos[ee,0]-ex,pos[ee,1]-ey)<0.5
            if at.any():
                for i in np.where(ee)[0][at]: queues[e].append(int(i)); arrived[i]=True
        if trace_q: qhist.append([len(queues[e]) for e in range(3)])
    return (dep_t.max() if departed.all() else MAXT), flow, qhist

def gini(x):
    x=np.sort(np.asarray(x,dtype=float)); n=len(x)
    return (2*np.sum(np.arange(1,n+1)*x)- (n+1)*np.sum(x))/(n*np.sum(x)) if x.sum()>0 else 0.0

out={}
# Gini 均衡度
_,f_nearest,_=run(400,"nearest",0,seed=2026)
_,f_cong,_=run(400,"cong",3.0,seed=2026)
out["gini"]={"nearest":round(gini(f_nearest),3),"cong":round(gini(f_cong),3),
             "nearest_flow":f_nearest,"cong_flow":f_cong}
# 排队热图（cong）
T,f,qh=run(400,"cong",3.0,seed=2026,trace_q=True)
out["q_heat"]={"T":T,"q":[[int(x) for x in row] for row in qh[:min(len(qh),300)]]}
# 复杂度计时
out["timing"]={}
for N in [200,400,800,1600,3200]:
    t0=time.time()
    run(N,"cong",3.0,seed=2026)
    out["timing"][str(N)]=round(time.time()-t0,4)
# 5智能体算例（初始队列0）
agents=[(10.0,3.0),(18.0,4.0),(20.0,10.0),(4.0,10.0),(12.0,14.0)]
ex=[(0.0,8.0),(24.0,8.0),(12.0,0.0)]
d=[[round(float(np.hypot(a[0]-e[0],a[1]-e[1])),2) for e in ex] for a in agents]
assign=[int(np.argmin(row)) for row in d]
# 一步移动 dt=0.1
step=V0*DT
newpos=[]
for a,ai in zip(agents,assign):
    exx,eyy=ex[ai]; dx=exx-a[0]; dy=eyy-a[1]; dist=np.hypot(dx,dy)
    if dist<1e-6: newpos.append([round(a[0],3),round(a[1],3)])
    else: newpos.append([round(a[0]+dx/dist*step,3),round(a[1]+dy/dist*step,3)])
out["example"]={"agents":agents,"d":d,"assign":assign,"newpos":newpos,"step":step}
json.dump(out,open("/tmp/evac_extra.json","w"),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1)[:2000])

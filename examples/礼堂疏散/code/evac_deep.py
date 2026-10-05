# -*- coding: utf-8 -*-
"""礼堂疏散深版：基线 / 分段重分配 / 全程动态重分配 + 密度与速度敏感性。"""
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

def run(N, policy, lam, reassign_step, speed, seed):
    rng=np.random.default_rng(seed); pos=make_positions(seed,N)
    assign=np.full(N,-1,int); arrived=np.zeros(N,bool); departed=np.zeros(N,bool); dep_t=np.full(N,-1.0)
    queues=[deque() for _ in range(3)]; frac=[0.0]*3; flow=[0,0,0]
    for k in range(int(MAXT/DT)+1):
        t=k*DT
        for e in range(3):
            frac[e]+=EXITS[e][2]*FLOW*DT; no=int(frac[e])
            for _ in range(no):
                if queues[e]:
                    i=queues[e].popleft(); departed[i]=True; dep_t[i]=t; flow[e]+=1
            frac[e]-=no
        if departed.all(): break
        d=np.stack([np.hypot(pos[:,0]-EXITS[e][0],pos[:,1]-EXITS[e][1]) for e in range(3)],1)
        if policy=="nearest":
            assign[assign<0]=np.argmin(d,1)[assign<0]
        else:
            if reassign_step is None or k%reassign_step==0:
                cost=d+lam*np.array([len(queues[e]) for e in range(3)])[None,:]
                assign[~arrived]=np.argmin(cost,1)[~arrived]
            else:
                assign[assign<0]=np.argmin(d,1)[assign<0]
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
    return (dep_t.max() if departed.all() else MAXT), flow

def mc(N, policy, lam, rs, speed, seeds):
    T=[]; F=[]
    for s in seeds:
        t,f=run(N,policy,lam,rs,speed,s); T.append(t); F.append(f)
    return np.mean(T),np.std(T),np.mean(F,axis=0)

if __name__=="__main__":
    seeds=list(range(2026,2036))
    r={}
    # 主结果
    r["nearest"]={"T":mc(400,"nearest",0,None,1.34,seeds)[:2]}
    r["cong"]={"T":mc(400,"cong",3.0,1,1.34,seeds)[:2]}
    # 消融
    r["abl"]={
      "静态最近出口": mc(400,"nearest",0,None,1.34,seeds)[0],
      "分段重分配(每40步)": mc(400,"cong",3.0,40,1.34,seeds)[0],
      "全程动态(每1步)": mc(400,"cong",3.0,1,1.34,seeds)[0],
    }
    # 敏感性 密度
    r["dens"]={N: mc(N,"cong",3.0,1,1.34,seeds)[0] for N in [200,300,400,500]}
    r["dens_base"]={N: mc(N,"nearest",0,None,1.34,seeds)[0] for N in [200,300,400,500]}
    # 敏感性 速度
    r["speed"]={v: mc(400,"cong",3.0,1,float(v),seeds)[0] for v in [1.0,1.2,1.34,1.5,1.6]}
    json.dump({k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in r.items()},
              open("/tmp/evac_deep.json","w"),ensure_ascii=False,indent=2)
    print(json.dumps({k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in r.items()},ensure_ascii=False,indent=1)[:1200])

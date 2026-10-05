# -*- coding: utf-8 -*-
"""礼堂疏散仿真：整数 FIFO 队列，离场以出口容量逐个服务。"""
import numpy as np, json
from collections import deque

W,H=24.0,16.0
EXITS=[("E1",(0.0,8.0),1.6),("E2",(24.0,8.0),1.2),("E3",(12.0,0.0),0.8)]
N=400; V0=1.34; FLOW=0.73; DT=0.1; MAXT=900.0
def cap(e): return max(1, int(round(e[2]*FLOW*DT)))  # 每步可服务人数（取整，E3=0.8*0.73*0.1=0.058→1? 太小）
# 注意：DT=0.1 时 E3 每步容量 0.058 人 → 需要累计。改用累计分数容量。

def make_positions(seed):
    rng=np.random.default_rng(seed)
    parts=[]
    for cx,cy,w in [(12,3,0.60),(19,8,0.25),(5,8,0.15)]:
        m=int(round(N*w))
        p=rng.normal(loc=(cx,cy),scale=(2.2,1.6),size=(m,2))
        p[:,0]=np.clip(p[:,0],0.5,W-0.5); p[:,1]=np.clip(p[:,1],0.5,H-0.5)
        parts.append(p)
    return np.concatenate(parts)[:N].copy()

def run(policy, lam, seed):
    rng=np.random.default_rng(seed)
    pos=make_positions(seed)
    assign=np.full(N,-1,int)
    arrived=np.zeros(N,bool)      # 已到出口、在排队
    departed=np.zeros(N,bool)
    dep_t=np.full(N,-1.0)
    queues=[deque() for _ in range(3)]
    frac=[0.0,0.0,0.0]            # 每出口累计分数容量
    flow_out=[0,0,0]              # 实际离开人数
    remain=[]
    for k in range(int(MAXT/DT)+1):
        t=k*DT
        remain.append(int((~departed).sum()))
        # 出口服务：累计容量，整数部分放行
        for e in range(3):
            frac[e]+=EXITS[e][2]*FLOW*DT
            n_out=int(frac[e])
            for _ in range(n_out):
                if queues[e]:
                    i=queues[e].popleft(); departed[i]=True; dep_t[i]=t; flow_out[e]+=1
            frac[e]-=n_out
        if departed.all(): break
        # 分配
        if policy=="nearest":
            d=np.stack([np.hypot(pos[:,0]-EXITS[e][1][0],pos[:,1]-EXITS[e][1][1]) for e in range(3)],1)
            assign[assign<0]=np.argmin(d,1)[assign<0]
        else:
            d=np.stack([np.hypot(pos[:,0]-EXITS[e][1][0],pos[:,1]-EXITS[e][1][1]) for e in range(3)],1)
            cost=d+lam*np.array([len(queues[e]) for e in range(3)])[None,:]
            assign[~arrived]=np.argmin(cost,1)[~arrived]
        # 移动（未到达、未离开者）
        moving=~arrived & ~departed
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][1]
            dx=ex-pos[ee,0]; dy=ey-pos[ee,1]
            dist=np.hypot(dx,dy)
            s=V0*DT
            pos[ee,0]+=np.where(dist>1e-6, dx/dist*s, 0)
            pos[ee,1]+=np.where(dist>1e-6, dy/dist*s, 0)
            pos[ee,0]=np.clip(pos[ee,0],0,W); pos[ee,1]=np.clip(pos[ee,1],0,H)
        # 到达出口进入队列
        for e in range(3):
            ee=(assign==e)&moving
            if not ee.any(): continue
            ex,ey=EXITS[e][1]
            dist=np.hypot(pos[ee,0]-ex,pos[ee,1]-ey)
            at=dist<0.5
            if at.any():
                for i in np.where(ee)[0][at]:
                    queues[e].append(int(i)); arrived[i]=True
    total=dep_t.max() if departed.all() else MAXT
    return total, flow_out, np.array(remain)

def metrics(policy, lam, seeds):
    Ts=[]; flows=[]
    for s in seeds:
        t,f,_=run(policy,lam,s); Ts.append(t); flows.append(f)
    return np.array(Ts), np.mean(flows,axis=0)

if __name__=="__main__":
    seeds=list(range(2026,2036))
    Tb,Sb=metrics("nearest",0,seeds)
    Tp,Sp=metrics("cong",3.0,seeds)
    print("nearest T mean±std:", round(Tb.mean(),1), round(Tb.std(),1), "flow", [round(x) for x in Sb])
    print("cong    T mean±std:", round(Tp.mean(),1), round(Tp.std(),1), "flow", [round(x) for x in Sp])
    print("improve%:", round((Tb.mean()-Tp.mean())/Tb.mean()*100,1))
    json.dump({"nearest_T":[float(x) for x in Tb],"cong_T":[float(x) for x in Tp],
               "nearest_flow":[float(x) for x in Sb],"cong_flow":[float(x) for x in Sp]},
              open("/tmp/evac_results.json","w"),ensure_ascii=False,indent=2)

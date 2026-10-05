# -*- coding: utf-8 -*-
"""正确实现 IQL vs VDN（N=15 疏散），修复：预动作状态、Q裁剪、小学习率。"""
import numpy as np, json
W,H=24.0,16.0; EXITS=[(0.,8.,1.6),(24.,8.,1.2),(12.,0.,0.8)]; V0=1.34; FLOW=0.73; DT=0.3; N=15
S=16; A=3
def state(P,q):
    D=np.hypot(P[:,0:1]-np.array([e[0] for e in EXITS])[None,:], P[:,1:2]-np.array([e[1] for e in EXITS])[None,:])
    dmin=D.min(1); e=D.argmin(1); qe=np.array(q)[e]
    return ((dmin/24*4).astype(int).clip(0,3))*4+((qe/15*4).astype(int).clip(0,3))
def make_pos(seed):
    rng=np.random.default_rng(seed); P=np.column_stack([rng.uniform(1,23,N),rng.uniform(1,15,N)]); return P
def gini(x):
    x=np.sort(np.asarray(x,float)); n=len(x); return (2*np.sum(np.arange(1,n+1)*x)-(n+1)*np.sum(x))/(n*np.sum(x)) if x.sum()>0 else 0
def train(algo,seed,eps=150,lr=0.05,gam=0.95):
    rng=np.random.default_rng(seed); Q=np.zeros((S,A)); e=1.0; crv=[]
    for ep in range(eps):
        P=make_pos(seed+ep); arrv=np.zeros(N,bool); dept=np.zeros(N,bool); q=[0.,0.,0.]; fr=[0.,0.,0.]; rsum=0.0
        for st in range(1500):
            for x in range(3):
                fr[x]+=EXITS[x][2]*FLOW*DT; no=int(fr[x]); fr[x]-=no
                for _ in range(no):
                    if q[x]>0: q[x]-=1; # 离场（不追踪身份，流量另计）
            if dept.all(): break
            s0=state(P,q)
            a=np.array([int(rng.integers(0,3)) if rng.random()<e else int(np.argmax(Q[s])) for s in s0])
            # 移动
            for i in range(N):
                if arrv[i] or dept[i]: continue
                exx,eyy=EXITS[a[i]][0],EXITS[a[i]][1]; dx=exx-P[i,0]; dy=eyy-P[i,1]; d=np.hypot(dx,dy)
                P[i,0]+=dx/d*V0*DT; P[i,1]+=dy/d*V0*DT
                if d<0.5: arrv[i]=True; q[a[i]]+=1
            # 服务
            for x in range(3):
                for _ in range(int(EXITS[x][2]*FLOW*DT)):
                    if q[x]>0: q[x]-=1
            s1=state(P,q)
            if algo=="iql":
                for i in range(N):
                    if dept[i]: continue
                    r=-0.01 if not arrv[i] else 0.0
                    Q[s0[i],a[i]]+=lr*(r+gam*Q[s1[i]].max()-Q[s0[i],a[i]]); rsum+=r
            else:
                active=np.where(~dept)[0]
                qtot=Q[s0[active],a[active]].sum()
                qnext=Q[s1[active]].max(1).sum()
                r=-0.01*len(active)   # 全局奖励：当前仍在内人数
                td=r+gam*qnext-qtot
                Q[s0[active],a[active]]+=lr*(td/len(active))
                rsum+=r
        e=max(0.05,e*0.98); crv.append(rsum)
        Q=np.clip(Q,-2,2)
    return Q,crv
def evalc(Q,seed):
    P=make_pos(seed+999); arrv=np.zeros(N,bool); dept=np.zeros(N,bool); q=[0.,0.,0.]; fr=[0.,0.,0.]; flow=[0,0,0]
    for st in range(2000):
        for x in range(3):
            fr[x]+=EXITS[x][2]*FLOW*DT; no=int(fr[x]); fr[x]-=no
            for _ in range(no):
                if q[x]>0: q[x]-=1; flow[x]+=1
        if dept.all(): break
        ss=state(P,q); a=np.array([int(np.argmax(Q[s])) for s in ss])
        for i in range(N):
            if arrv[i] or dept[i]: continue
            exx,eyy=EXITS[a[i]][0],EXITS[a[i]][1]; dx=exx-P[i,0]; dy=eyy-P[i,1]; d=np.hypot(dx,dy)
            P[i,0]+=dx/d*V0*DT; P[i,1]+=dy/d*V0*DT
            if d<0.5: arrv[i]=True; q[a[i]]+=1
    return st*DT, gini(flow), [int(x) for x in flow]
out={}
for algo in ["iql","vdn"]:
    Q,c=train(algo,1,150); t,g,f=evalc(Q,1)
    out[algo]={"T":round(t,1),"gini":round(g,3),"flow":f,"curve":c}
    print(algo,"T",round(t,1),"gini",round(g,3),"flow",f,"curve_last",round(c[-1],2))
json.dump({"iql":{"T":out["iql"]["T"],"gini":out["iql"]["gini"],"flow":out["iql"]["flow"]},
           "vdn":{"T":out["vdn"]["T"],"gini":out["vdn"]["gini"],"flow":out["vdn"]["flow"]}},open("/tmp/vdn2_res.json","w"))
json.dump({"iql_curve":out["iql"]["curve"],"vdn_curve":out["vdn"]["curve"]},open("/tmp/vdn2_curves.json","w"))
